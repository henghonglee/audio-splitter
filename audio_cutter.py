#!/usr/bin/env python3

import argparse
import os
import sys
import wave
import struct
from pathlib import Path

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Warning: pydub not available. Only WAV files supported.", file=sys.stderr)


class AudioCutter:
    def __init__(self, input_file):
        self.input_file = Path(input_file)
        if not self.input_file.exists():
            raise FileNotFoundError(f"Audio file not found: {input_file}")
        
        if PYDUB_AVAILABLE:
            try:
                self.audio = AudioSegment.from_file(str(self.input_file))
                self.backend = 'pydub'
            except Exception as e:
                raise ValueError(f"Could not load audio file with pydub: {e}")
        else:
            # Fallback to wave module for WAV files only
            if not str(self.input_file).lower().endswith('.wav'):
                raise ValueError("Only WAV files are supported without pydub. Install FFmpeg and pydub for other formats.")
            
            try:
                self.wave_file = wave.open(str(self.input_file), 'rb')
                self.sample_rate = self.wave_file.getframerate()
                self.channels = self.wave_file.getnchannels()
                self.sample_width = self.wave_file.getsampwidth()
                self.total_frames = self.wave_file.getnframes()
                self.duration_ms = int((self.total_frames / self.sample_rate) * 1000)
                self.backend = 'wave'
            except Exception as e:
                raise ValueError(f"Could not load WAV file: {e}")
    
    def cut_from_front(self, duration_ms):
        if duration_ms <= 0:
            raise ValueError("Duration must be positive")
        if duration_ms >= self.get_duration():
            raise ValueError("Duration cannot be longer than the audio file")
        
        if self.backend == 'pydub':
            return self.audio[duration_ms:]
        else:
            return self._wav_cut_from_front(duration_ms)
    
    def cut_from_back(self, duration_ms):
        if duration_ms <= 0:
            raise ValueError("Duration must be positive")
        if duration_ms >= self.get_duration():
            raise ValueError("Duration cannot be longer than the audio file")
        
        if self.backend == 'pydub':
            return self.audio[:-duration_ms]
        else:
            return self._wav_cut_from_back(duration_ms)
    
    def cut_from_middle(self, start_ms, end_ms):
        if start_ms < 0 or end_ms < 0:
            raise ValueError("Start and end times must be non-negative")
        if start_ms >= end_ms:
            raise ValueError("Start time must be before end time")
        if end_ms > self.get_duration():
            raise ValueError("End time cannot be beyond the audio length")
        
        if self.backend == 'pydub':
            before_cut = self.audio[:start_ms]
            after_cut = self.audio[end_ms:]
            return before_cut + after_cut
        else:
            return self._wav_cut_from_middle(start_ms, end_ms)
    
    def extract_segment(self, start_ms, end_ms):
        if start_ms < 0 or end_ms < 0:
            raise ValueError("Start and end times must be non-negative")
        if start_ms >= end_ms:
            raise ValueError("Start time must be before end time")
        if end_ms > self.get_duration():
            raise ValueError("End time cannot be beyond the audio length")
        
        if self.backend == 'pydub':
            return self.audio[start_ms:end_ms]
        else:
            return self._wav_extract_segment(start_ms, end_ms)
    
    def get_duration(self):
        if self.backend == 'pydub':
            return len(self.audio)
        else:
            return self.duration_ms
    
    def save_audio(self, audio_data, output_file, format=None):
        output_path = Path(output_file)
        
        if self.backend == 'pydub':
            if format is None:
                format = output_path.suffix[1:].lower() if output_path.suffix else 'mp3'
            try:
                audio_data.export(str(output_path), format=format)
                return output_path
            except Exception as e:
                raise ValueError(f"Could not save audio file: {e}")
        else:
            # Save WAV file using wave module
            if not str(output_path).lower().endswith('.wav'):
                output_path = output_path.with_suffix('.wav')
            
            try:
                with wave.open(str(output_path), 'wb') as output_wav:
                    output_wav.setnchannels(self.channels)
                    output_wav.setsampwidth(self.sample_width)
                    output_wav.setframerate(self.sample_rate)
                    output_wav.writeframes(audio_data)
                return output_path
            except Exception as e:
                raise ValueError(f"Could not save WAV file: {e}")
    
    def _wav_cut_from_front(self, duration_ms):
        start_frame = int((duration_ms / 1000) * self.sample_rate)
        self.wave_file.setpos(start_frame)
        remaining_frames = self.total_frames - start_frame
        return self.wave_file.readframes(remaining_frames)
    
    def _wav_cut_from_back(self, duration_ms):
        cut_frames = int((duration_ms / 1000) * self.sample_rate)
        keep_frames = self.total_frames - cut_frames
        self.wave_file.setpos(0)
        return self.wave_file.readframes(keep_frames)
    
    def _wav_cut_from_middle(self, start_ms, end_ms):
        start_frame = int((start_ms / 1000) * self.sample_rate)
        end_frame = int((end_ms / 1000) * self.sample_rate)
        
        # Get the part before the cut
        self.wave_file.setpos(0)
        before_data = self.wave_file.readframes(start_frame)
        
        # Get the part after the cut
        self.wave_file.setpos(end_frame)
        after_data = self.wave_file.readframes(self.total_frames - end_frame)
        
        return before_data + after_data
    
    def _wav_extract_segment(self, start_ms, end_ms):
        start_frame = int((start_ms / 1000) * self.sample_rate)
        end_frame = int((end_ms / 1000) * self.sample_rate)
        
        self.wave_file.setpos(start_frame)
        return self.wave_file.readframes(end_frame - start_frame)


def parse_time(time_str):
    if time_str.endswith('s'):
        return int(float(time_str[:-1]) * 1000)
    elif time_str.endswith('ms'):
        return int(time_str[:-2])
    elif time_str.endswith('m'):
        return int(float(time_str[:-1]) * 60 * 1000)
    elif ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:
            minutes, seconds = parts
            return int(float(minutes) * 60 * 1000 + float(seconds) * 1000)
        elif len(parts) == 3:
            hours, minutes, seconds = parts
            return int(float(hours) * 3600 * 1000 + float(minutes) * 60 * 1000 + float(seconds) * 1000)
    else:
        return int(float(time_str) * 1000)


def format_duration(duration_ms):
    total_seconds = duration_ms / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
    else:
        return f"{minutes:02d}:{seconds:06.3f}"


def main():
    parser = argparse.ArgumentParser(
        description="Cut audio files by removing sections from front, back, or middle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Time format examples:
  5s          - 5 seconds
  15m         - 15 minutes
  500ms       - 500 milliseconds  
  1:30        - 1 minute 30 seconds
  1:23:45     - 1 hour 23 minutes 45 seconds
  75.5        - 75.5 seconds

Usage examples:
  # Remove first 10 seconds
  python audio_cutter.py input.mp3 --cut-front 10s -o output.mp3
  
  # Remove last 5 seconds
  python audio_cutter.py input.mp3 --cut-back 5s -o output.mp3
  
  # Remove middle section from 1:00 to 2:30
  python audio_cutter.py input.mp3 --cut-middle 1:00 2:30 -o output.mp3
  
  # Extract only the middle section from 1:00 to 2:30
  python audio_cutter.py input.mp3 --extract 1:00 2:30 -o output.mp3
        """
    )
    
    parser.add_argument("input_file", help="Input audio file")
    parser.add_argument("-o", "--output", required=True, help="Output audio file")
    
    # Cutting operations (mutually exclusive)
    cut_group = parser.add_mutually_exclusive_group(required=True)
    cut_group.add_argument("--cut-front", metavar="DURATION", 
                          help="Remove specified duration from the front")
    cut_group.add_argument("--cut-back", metavar="DURATION",
                          help="Remove specified duration from the back")
    cut_group.add_argument("--cut-middle", nargs=2, metavar=("START", "END"),
                          help="Remove section between START and END times")
    cut_group.add_argument("--extract", nargs=2, metavar=("START", "END"),
                          help="Extract only the section between START and END times")
    
    parser.add_argument("--format", help="Output format (mp3, wav, etc.). Auto-detected from extension if not specified")
    parser.add_argument("--info", action="store_true", help="Show audio file information")
    
    args = parser.parse_args()
    
    try:
        cutter = AudioCutter(args.input_file)
        
        if args.info:
            duration = cutter.get_duration()
            print(f"Audio duration: {format_duration(duration)} ({duration} ms)")
        
        if args.cut_front:
            duration_ms = parse_time(args.cut_front)
            result_audio = cutter.cut_from_front(duration_ms)
            print(f"Cutting {format_duration(duration_ms)} from front")
            
        elif args.cut_back:
            duration_ms = parse_time(args.cut_back)
            result_audio = cutter.cut_from_back(duration_ms)
            print(f"Cutting {format_duration(duration_ms)} from back")
            
        elif args.cut_middle:
            start_ms = parse_time(args.cut_middle[0])
            end_ms = parse_time(args.cut_middle[1])
            result_audio = cutter.cut_from_middle(start_ms, end_ms)
            print(f"Cutting section from {format_duration(start_ms)} to {format_duration(end_ms)}")
            
        elif args.extract:
            start_ms = parse_time(args.extract[0])
            end_ms = parse_time(args.extract[1])
            result_audio = cutter.extract_segment(start_ms, end_ms)
            print(f"Extracting section from {format_duration(start_ms)} to {format_duration(end_ms)}")
        
        output_path = cutter.save_audio(result_audio, args.output, args.format)
        print(f"Saved to: {output_path}")
        
        # Calculate output duration correctly based on backend
        if cutter.backend == 'pydub':
            output_duration_ms = len(result_audio)
        else:
            # For WAV files, calculate duration from raw audio data
            bytes_per_sample = cutter.sample_width * cutter.channels
            samples = len(result_audio) // bytes_per_sample
            output_duration_ms = int((samples / cutter.sample_rate) * 1000)
        
        print(f"Output duration: {format_duration(output_duration_ms)} ({output_duration_ms} ms)")
        
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
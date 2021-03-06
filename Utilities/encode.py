#!/usr/bin/env python
# coding: utf-8
import os
import sys
import argparse
import time
import subprocess
import signal
import tempfile
import ffpb


class style():
    green = '\033[1m\033[32m'
    magenta = '\033[1m\033[35m'
    yellow = '\033[1m\033[93m'
    blue = '\033[1m\033[34m'
    white = '\033[1m\033[37m'
    red = '\033[1m\033[31m'
    reset = '\033[0m'


parser = argparse.ArgumentParser(prog='encoder.py', formatter_class=argparse.ArgumentDefaultsHelpFormatter, description='Reduce video size with FFmpeg')
parser.add_argument('input', type=str, help='Input file')
parser.add_argument('size', type=int, help='Desired output size in MB')
parser.add_argument('-f', default='mkv', help='Output format (mp4, mkv, etc)', metavar='format')
parser.add_argument('-p', type=str, default='medium', help='encoder preset', metavar='preset')
parser.add_argument('-e', choices=["h264", "vp9", "hevc", "av1"], default='h264', help='Output video codec')

parser.add_argument('-o', type=str, help='Output file', metavar='output')


if __name__ == '__main__':
    os.system("")  # Because Windows is stupid and doesn't like ANSI colors
    args = parser.parse_args()

    def signal_handler(signal, frame):
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)


def print_slow(text, duration):
    print('\n' + str(text))
    time.sleep(duration)


def calculate_bitrate(filename, size):
    try:
        proc = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filename], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(style.red + '\nffprobe error:\n' + style.reset + e.output.decode('utf-8'))
        sys.exit(1)

    duration = float(proc.stdout.decode('utf-8'))

    exp_br = int(float(size) * 1024 * 1024 * 8 / duration / 1000)
    final_br = exp_br - (exp_br * 0.020)
    text_br = str(final_br) + 'k'

    return text_br


def get_size_notation(size):
    fltsize = int(size)
    if fltsize >= 1024:
        realsize = str(float(fltsize / 1024)) + 'GB'
    else:
        realsize = str(size) + 'MB'
    return str(realsize)


def outfile(filename):
    if args.o is None:
        return os.path.abspath(filename) + '-' + get_size_notation(args.size) + '.' + args.f
    else:
        return os.path.abspath(args.o)


def do_conversion():
    if os.path.isdir(args.input):
        if args.o is not None:
            print(style.red + 'Syntax Error: "-o" argument must not be used when converting entire directories' + style.reset)
            sys.exit(1)
        mov = [entry.path for entry in os.scandir(args.input) if entry.is_file()]
    elif os.path.isfile(args.input):
        mov = [args.input]
        if args.o is not None:
            print(style.yellow + 'WARNING: ' + style.white + 'Using "-o" will override the "-f" argument' + style.reset)

    for filename in mov:

        if args.e == 'h264':
            arg_list = ['-hide_banner', '-y', '-i', os.path.abspath(filename), '-c:v', 'libx264', '-preset', args.p, '-b:v', calculate_bitrate(filename, args.size), '-an', '-pass', '1', '-f', 'null', os.devnull]
            arg_pass = ['-hide_banner', '-y', '-i', os.path.abspath(filename), '-c:v', 'libx264', '-preset', args.p, '-b:v', calculate_bitrate(filename, args.size), '-map', '0', '-c:a', 'copy', '-pass', '2', outfile(filename)]
        elif args.e == 'hevc':
            arg_list = ['-hide_banner', '-y', '-i', os.path.abspath(filename), '-c:v', 'libx265', '-preset', args.p, '-b:v', calculate_bitrate(filename, args.size), '-an', '-pass', '1', '-f', 'null', os.devnull]
            arg_pass = ['-hide_banner', '-y', '-i', os.path.abspath(filename), '-c:v', 'libx265', '-preset', args.p, '-b:v', calculate_bitrate(filename, args.size), '-map', '0', '-c:a', 'copy', '-pass', '2', outfile(filename)]
        elif args.e == 'vp9':
            arg_list = ['-hide_banner', '-y', '-i', os.path.abspath(filename), '-c:v', 'libvpx-vp9', '-preset', args.p, '-b:v', calculate_bitrate(filename, args.size), '-row-mt', '1', '-an', '-pass', '1', '-f', 'null', os.devnull]
            arg_pass = ['-hide_banner', '-y', '-i', os.path.abspath(filename), '-c:v', 'libvpx-vp9', '-preset', args.p, '-b:v', calculate_bitrate(filename, args.size), '-row-mt', '1', '-map', '0', '-c:a', 'copy', '-pass', '2', outfile(filename)]
        elif args.e == 'av1':
            arg_list = ['-hide_banner', '-y', '-i', os.path.abspath(filename), '-c:v', 'libaom-av1', '-preset', args.p, '-b:v', calculate_bitrate(filename, args.size), '-row-mt', '1', '-an', '-pass', '1', '-f', 'null', os.devnull]
            arg_pass = ['-hide_banner', '-y', '-i', os.path.abspath(filename), '-c:v', 'libaom-av1', '-preset', args.p, '-b:v', calculate_bitrate(filename, args.size), '-row-mt', '1', '-map', '0', '-c:a', 'copy', '-pass', '2', outfile(filename)]

        print_slow((style.white + 'Input file: ' + style.reset + os.path.abspath(filename)), 0.5)
        print_slow((style.white + 'Output File: ' + style.reset + outfile(filename)), 0.5)
        print_slow((style.white + 'Desired final file size: ' + style.reset + '~' + get_size_notation(args.size)), 0.5)
        print_slow((style.white + 'FFmpeg will use the ' + style.blue + args.e + style.white + ' encoder ' + style.white + 'with the ' + style.magenta + args.p + style.white + ' preset' + style.reset), 0.5)
        print_slow((style.white + 'Expected video bitrate will be: ' + style.reset + '~' + calculate_bitrate(filename, args.size)), 0.5)
        print_slow(style.blue + 'Audio bitrate will remain as-is\n' + style.reset, 0.5)

        tmp = tempfile.TemporaryDirectory()
        os.chdir(tmp.name)

        print_slow('Running ' + style.green + '1st' + style.reset + ' pass...', 0.5)
        ffpb.main(argv=arg_list)

        print_slow('\nRunning ' + style.green + '2nd' + style.reset + ' pass...', 0.5)
        ffpb.main(argv=arg_pass)

        print_slow(style.white + 'Cleaning up...' + style.reset, 0.5)
    time.sleep(0.5)
    print(style.green + 'Done' + style.reset)
    sys.exit(0)


do_conversion()

#!/usr/local/bin/python3

import os
import sys

# Opens the specified file and returns its file descriptor.
def open_file(filename, mode):
    fd = os.open(filename, mode)
    return fd

# Returns the size of the file with the given file descriptor.
def get_file_size(fd):
    size = os.lseek(fd, 0, os.SEEK_END)
    os.lseek(fd, 0, os.SEEK_SET)  # Reset the file pointer to the beginning after getting size.
    return size

# Generator function to read content from the file in blocks.
def read_block(fd, block_size = 2500):
    while True:
        data = os.read(fd, block_size)
        if data:
            yield data
        else:
            break

# Writes data to the specified file descriptor.
def write_content(fd, data):
    bytes_written = 0
    while (bytes_written < len(data)):
        written = os.write(fd, data[bytes_written:])
        bytes_written += written
    return bytes_written

# Encodes and frames the filename and content for archiving.
def framer(filename, content):
    name_bytes = filename.encode()  # Convert filename to bytes.
    name_length = len(name_bytes)
    name_length_bytes = name_length.to_bytes(2, 'big')  # Filename length: 2 bytes
    content_length_bytes = len(content).to_bytes(8, 'big')  # Content length: 8 bytes

    # Return the combined byte stream: [name_length | name | content_length | content]
    return name_length_bytes + name_bytes + content_length_bytes + content

# Decodes the framed data to retrieve the original filename and content.
def deframer(buffer):
    filename_length = int.from_bytes(buffer[:2], 'big')
    filename = buffer[2:2+filename_length].decode()
    content_length = int.from_bytes(buffer[2+filename_length:10+filename_length], 'big')
    content = buffer[10+filename_length:10+filename_length+content_length]
    return filename, content

# Archives the specified files and writes to stdout.
def create(files):
    for fyle in files:
        fd = open_file(fyle, os.O_RDONLY)
        content = b"".join(read_block(fd))  # Combine all blocks to form the content.
        framed_data = framer(fyle, content)
        write_content(1, framed_data)  # Write to stdout (file descriptor 1).
        os.close(fd)

# Extracts and restores files from the archived data read from stdin.
def extract():
    buffer = b""
    while True:
        data = os.read(0, 1024)
        if not data:
            break
        buffer += data

        while len(buffer) > 10:  # Minimum frame length is 10 (2 for filename length and 8 for content length).
            filename_length = int.from_bytes(buffer[:2], 'big')
            
            # Check if we have enough data for a full frame.
            if len(buffer) < 2 + filename_length + 8:
                break

            filename = buffer[2:2 + filename_length].decode(errors='ignore')  # Use 'ignore' to handle decode errors.
            content_length = int.from_bytes(buffer[2 + filename_length:10 + filename_length], 'big')
            
            # Check if we have all the content.
            if len(buffer) < 10 + filename_length + content_length:
                break

            content = buffer[10 + filename_length:10 + filename_length + content_length]
            
            fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            os.write(fd, content)
            os.close(fd)

            buffer = buffer[10 + filename_length + content_length:]

# Reports errors by writing the message to stderr.
def report_error(message):
    os.write(2, (message + '\n').encode())

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "c":  # Create mode
        files = sys.argv[2:]
        create(files)
    elif mode == "x":  # Extract mode
        extract()

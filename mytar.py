import os

# return file descriptor
def open_file(filename, mode):
    fd = os.open(filename, mode)
    return fd

# returns file size
def get_file_size(fd):
    size = os.lseek(fd, 0, os.SEEK_END)
    return size

# reads file content in blocks of 2500 bytes
def read_block(fd, block_size = 2500):
    while 1:
        data = os.read(fd, block_size)

        if data:
            yield data
        else:
            break
    
# write data to destination fd
def write_content(fd, data):
    bytes_written = 0

    while (bytes_written < len(data)):
        written = os.write(fd, data[bytes_written:])
        bytes_written += written
    return bytes_written
    
# encodes and frames data for archiving
def framer(filename, content):
    # check if filename is in bytes, if not convert it
    name_bytes = filename if isinstance(filename, bytes) else filename.encode()
    name_length = len(filename)
    name_length_bytes = name_length.to_bytes(2, 'big') # constrain filename to 2 bytes
    content_length = len(content)
    content_length_bytes = content_length.to_bytes(8, 'big') # constrain content length to 8 bytes

    return name_length_bytes + name_bytes + content_length_bytes + content
    
# decodes framed data
def deframer(buffer):
    filename_length = int.from_bytes(buffer[:2], 'big')
    filename = buffer[2:2+filename_length].decode()
    content_length = int.from_bytes(buffer[2+filename_length:10+filename_length], 'big')
    content = buffer[10+filename_length:10+filename_length+content_length]
    return filename, content
     
# archives files
def create(files):
    # iterate through files
    for fyle in files:
        # get file descriptor
        fd = open_file(fyle, os.O_RDONLY)
        content = b""
        
        #read file in blocks until EOF
        for block in read_block(fd):
            content += block

        framed_data = framer(fyle, content)

        # write framed data to stdout
        write_content(1, framed_data)

        # close fd
        os.close(fd)
    
# extracts archived files
def extract():
    buffer = b""
    
    while True:
        data = os.read(0, 1024)
        if not data:
            break
        
        buffer += data

        while buffer:
            filename, content = deframer(buffer)
            fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            os.write(fd, content)
            os.close(fd)
            
            frame_length = 10 + len(filename.encode()) + len(content)
            buffer = buffer[frame_length:]

    
    
# reports error message to stderr
def report_error(message):
    os.write(2, (message + '\n').encode())
    
if __name__ == "__main__":

    mode = sys.argv[1]
    
    # Create mode
    if mode == "c":
        files = sys.argv[2:]
        create(files)
    
    # Extract mode
    elif mode == "x":
        extract()

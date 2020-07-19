

def convert(data:bytes, chardic):
    str_data = str(data)[2:][:-1] # ignore the nasty b' and the ' at the end
    i=0
    str_data = str_data.replace('\\r\\n', '\n') # line breaks
    while i<len(str_data):
        if str_data[i]=='\\': # encoding failure detected
            fail_str = str_data[i+1:i+4]
            try:
                replace = chardic[fail_str]
                str_data = str_data[:i] + replace + str_data[i+4:]
            except:
                str_data = str_data[:i] + "/" + str_data[i+1:] 
        i+=1
    return str_data

import sys
import os
from   datetime import datetime
import json
import hashlib
import hmac
import http.client
from   xml.dom.minidom import parseString
import base64

## parse command line arguments
if len(sys.argv) != 3:
    raise ValueError("Please provide aws config name and request file name.")
 
config       = sys.argv[1]
request_file = sys.argv[2]

## parse config file
try:
    with open("./config.json") as json_data:
        config_data = json.load(json_data)[config]
except:
    raise ValueError("Could not find or parse config.json file.")

host       = config_data["host"]
port       = config_data["port"]
access_key = config_data["access_key"]
secret_key = config_data["secret_key"]
region     = config_data["region"]
service    = config_data["service"]
req_type   = config_data["req_type"]

if port:
    host = host + ':' + port

## parse and extend request
with open(request_file) as f:
    request = f.readlines()

if len(request) == 0:
    raise ValueError("Request file is empty.")

list_of_headers      = []
list_of_header_names = []
current_line = 3
for line in request[3:]:
    current_line = current_line + 1
    line = line.replace('\n','')
    if not line:
        break
    else:
        list_of_headers.append(line)
        list_of_header_names.append(line.split(':')[0])

content      = ''.join(request[current_line:])
content_hash = hashlib.sha256(content.encode()).hexdigest()

amz_time = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
amz_date = amz_time.split('T')[0]

list_of_headers.append("host:" + host)
list_of_headers.append("x-amz-content-sha256:" + content_hash)
list_of_headers.append("x-amz-date:" + amz_time)
list_of_header_names.append("host")
list_of_header_names.append("x-amz-content-sha256")
list_of_header_names.append("x-amz-date")

http_method = request[0].replace('\n','')
http_uri    = request[1].replace('\n','')
http_query  = request[2].replace('\n','')

if content:
    list_of_headers.append( "content-md5:" 
                            + base64.b64encode(hashlib.md5(content.encode("utf-8")).digest()).decode("utf-8")
                          )
    list_of_header_names.append("content-md5")

list_of_headers.sort()
list_of_header_names.sort()

aws_request = ( http_method                      + '\n'
                + http_uri                       + '\n'
                + http_query                     + '\n'
                + '\n'.join(list_of_headers)     + '\n'
                + '\n'
                + ';'.join(list_of_header_names) + '\n'
                + content_hash
              )

## create signature
string_to_sign = ( "AWS4-HMAC-SHA256" + '\n'
                   + amz_time + '\n'
                   + amz_date + '/' + region + '/' + service + '/' + req_type + '\n'
                   + hashlib.sha256(aws_request.encode()).hexdigest()
                 )

date_key                = hmac.new( ("AWS4" + secret_key).encode(),
                                    msg = amz_date.encode(),
                                    digestmod = hashlib.sha256
                                  ).digest()
date_region_key         = hmac.new( date_key,
                                    msg = region.encode(),
                                    digestmod = hashlib.sha256
                                  ).digest()
date_region_service_key = hmac.new( date_region_key,
                                    msg = service.encode(),
                                    digestmod = hashlib.sha256
                                  ).digest()
signing_key             = hmac.new( date_region_service_key,
                                    msg = "aws4_request".encode(),
                                    digestmod = hashlib.sha256
                                  ).digest()

signature = hmac.new( signing_key,
                      msg = string_to_sign.encode(),
                      digestmod = hashlib.sha256
                    ).hexdigest()

auth_header = ( "Authorization:"
                + "AWS4-HMAC-SHA256 " 
                + "Credential=" + access_key + '/' + amz_date + '/' + region + '/' 
                                + service    + '/' + req_type + ','
                + "SignedHeaders=" + ';'.join(list_of_header_names) + ','
                + "Signature=" + signature
              )
list_of_headers.append(auth_header)

if content:
    list_of_headers.append("Content-Type: application/xml")

## create and send request

conn = http.client.HTTPConnection(host)

if http_query:
    http_uri = http_uri + '?' + http_query

json_header = {}
for header in list_of_headers:
    key = header.split(":")[0]
    val = header.split(":")[1]
    if key=="host":
        if port:
            json_header[key] = val + ":" + port
        else:
            json_header[key] = val
    else:
            json_header[key] = val

conn.request(http_method, http_uri, content.encode("utf-8"), json_header)

# response
aws_response = conn.getresponse()

response = str(aws_response.status) + ' ' + aws_response.reason + '\n\n'

for header in aws_response.getheaders():
    response = response + ':'.join(header) + '\n'

response_data = aws_response.read().decode("utf-8") 
if response_data:
    xml_string = parseString(response_data).toprettyxml()
    xml_string = os.linesep.join([s for s in xml_string.splitlines() if s.strip()])
    response   = response + '\n' + xml_string   

## save request and response to file
request_file_without_ext = os.path.splitext(os.path.basename(request_file))[0]
formated_time            = datetime.now().strftime("%d%m%Y_%H%M%S")
request_file             = ( "./requests/"
                             + request_file_without_ext
                             + "_" + formated_time + ".txt"
                           )
response_file            = ( "./responses/"
                             + request_file_without_ext
                             + "_" + formated_time + ".txt"
                           )

if content:
    aws_request = aws_request + '\n\n' + content
with open(request_file , "w") as f:
    f.write(aws_request)

with open(response_file, "w") as f:
    f.write(response)

print(aws_request)
print("\n\n")
print(response)
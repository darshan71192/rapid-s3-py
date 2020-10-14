# rapid-s3-py

This python script is a quick and dirty tool made for rapid prototyping with S3 operations. It helps with creating low level requests as shown on Amazon's documetation page with manually setting http method, headers and xml content. It also shows s3 compatible 's response at low level with http code, headers and response xml. It shows final sent request and recieved response in terminal as well as stores them in subfolders with timestamps. It can be used with any S3 compatible server. It has limited functionality as of now. Please check script for details.


## How to use it

* Modify `config.json` file to edit/add your s3 compatible server configurations. 
* Create request file, 
  It should be in following format:
```
HTTP_METHOD                     (like GET,PUT,...)
uri                             (/<bucket_name>/<object_key>)
query                           (like tagging= ) 
                                Note: no leading '?'
additional_optional_headers     (like x-amz-bucket-object-lock-enabled:true) 
                                Note: don't put common headers like host, date, 
                                content-sha, content-md5 here. 
                                They will be added by script.                               
                                empty line (required)
xml body content
```
* Run the script in teminal at repo's root directory
```
pathon3 script.py <config_name> <request_file>

Example:
python3 script.py aws PutObjectLockConfiguration.txt
```
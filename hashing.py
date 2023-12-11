import hashlib
import base64
string="helloWorld123"

sha256_encoded_string=hashlib.sha256( base64.b64encode(string.encode('utf8'))).hexdigest()
print(sha256_encoded_string)
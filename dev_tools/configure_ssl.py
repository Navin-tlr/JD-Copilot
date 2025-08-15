import os
import ssl
import certifi

# Set SSL certificate variables to use certifi's bundle
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

print("SSL context configured to use certifi.")

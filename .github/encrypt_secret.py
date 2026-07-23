import base64, os, nacl.public
pubkey = base64.b64decode(os.environ['GH_PUBKEY'] + '==')
token = os.environ['NEW_TOKEN'].encode()
pk = nacl.public.PublicKey(pubkey)
print(base64.b64encode(nacl.public.SealedBox(pk).encrypt(token)).decode())

# Synthetic SMB negotiation fixtures

Hex encodes exact Direct TCP bytes; independent fixture assembly follows MS-SMB2
2.1, 2.2.1.2, 2.2.2 and 2.2.4. Not captured from a target; GUID/time and hostile
opaque buffer are synthetic. Success variants report SMB 2.0.2/2.1/3.0/3.0.2 and
signing bit combinations. Error variants deny authentication-dependent/unsupported
metadata; no fallback is permitted. No credential/hash/share/file data exists.

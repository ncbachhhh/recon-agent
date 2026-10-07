# FFUF fixtures

Sanitized source-shaped FFUF 2.1.0 `-json` stdout Result JSONL. Input byte values
are standard base64 (file `-of json` uses different input serialization). Reserved
192.0.2.10/example.test/outside.test values are offline data. Four separate
one-candidate HEAD invocations are stored together for fixture convenience.
Status/length/Location are tool facts, never confirmed vhosts or vulnerabilities.
FFUFHASH is internal metadata, ignored by normalization. No scanner/network used.

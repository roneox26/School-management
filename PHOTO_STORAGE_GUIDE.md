# Photo Storage Feature - PostgreSQL Integration

## Overview
এই ফিচারটি student এবং teacher এর জন্য photo upload, storage এবং retrieval সুবিধা প্রদান করে PostgreSQL ডাটাবেসে।

## Database Schema

### Photos Table (PostgreSQL)
```sql
CREATE TABLE photos (
    id TEXT PRIMARY KEY,
    entity_type TEXT,           -- 'student' or 'teacher'
    entity_id TEXT,             -- Student/Teacher ID
    photo_data BYTEA,           -- Binary photo data
    filename TEXT,              -- Original filename
    mime_type TEXT,             -- Image MIME type
    uploaded_at TIMESTAMP,      -- Upload timestamp
    uploaded_by TEXT,           -- Admin ID who uploaded
    UNIQUE(entity_type, entity_id)
);
```

### Photos Table (SQLite)
```sql
CREATE TABLE photos (
    id TEXT PRIMARY KEY,
    entity_type TEXT,
    entity_id TEXT,
    photo_data BLOB,
    filename TEXT,
    mime_type TEXT,
    uploaded_at TIMESTAMP,
    uploaded_by TEXT,
    UNIQUE(entity_type, entity_id)
);
```

## Features

### 1. Photo Upload
- **Endpoint**: `POST /upload_photo/<entity_type>/<entity_id>`
- **Supported Types**: PNG, JPG, JPEG, GIF
- **Max Size**: 16MB
- **Response**: JSON with photo_id

### 2. Photo Retrieval
- **Endpoint**: `GET /get_photo/<entity_type>/<entity_id>`
- **Returns**: Image file with correct MIME type
- **Fallback**: Placeholder image if no photo exists

### 3. Photo Deletion
- **Endpoint**: `POST /delete_photo/<entity_type>/<entity_id>`
- **Response**: JSON success/error message

### 4. Photo Check
- **Endpoint**: `GET /has_photo/<entity_type>/<entity_id>`
- **Returns**: Boolean indicating photo existence

## Usage Examples

### Upload Student Photo
```bash
curl -X POST \
  -F "photo=@student.jpg" \
  http://localhost:8000/upload_photo/student/student_id_123
```

### Upload Teacher Photo
```bash
curl -X POST \
  -F "photo=@teacher.jpg" \
  http://localhost:8000/upload_photo/teacher/teacher_id_456
```

### Get Photo
```bash
# Student photo
curl http://localhost:8000/get_photo/student/student_id_123 > student.jpg

# Teacher photo
curl http://localhost:8000/get_photo/teacher/teacher_id_456 > teacher.jpg
```

### Delete Photo
```bash
curl -X POST http://localhost:8000/delete_photo/student/student_id_123
```

## Frontend Integration

### HTML Form Example
```html
<form enctype="multipart/form-data">
    <input type="file" name="photo" accept="image/*">
    <button type="submit">Upload Photo</button>
</form>
```

### JavaScript Upload
```javascript
const formData = new FormData();
formData.append('photo', fileInput.files[0]);

fetch(`/upload_photo/student/${studentId}`, {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Photo uploaded:', data.photo_id);
    }
});
```

### Display Photo
```html
<img src="/get_photo/student/{{ student.id }}" alt="Student Photo">
```

## Teacher Edit Page Features

### Photo Management
- Upload new photo
- Preview before upload
- Delete existing photo
- Display current photo

### Form Fields
- Name
- Employee ID
- Phone
- Email
- Subject
- Salary
- Joining Date

## Student Edit Page Features

### Photo Management
- Upload new photo
- Preview before upload
- Delete existing photo
- Display current photo

### Form Fields
- Name
- Roll Number
- Class
- Phone
- Email
- Guardian Name
- Guardian Phone
- Date of Birth
- Address

## Database Configuration

### PostgreSQL Connection
```python
DATABASE_URL = "postgresql://user:password@localhost:5432/school_db"
```

### SQLite Connection
```python
DATABASE = "school_management.db"
```

## File Structure

### New Files Created
- `photo_storage.py` - Photo storage helper functions
- `photo_routes.py` - Photo-related API routes
- `templates/edit_teacher.html` - Teacher edit template with photo upload
- `templates/edit_student_photo.html` - Student edit template with photo upload

### Modified Files
- `main.py` - Added photo database schema and imports

## Security Features

1. **File Type Validation**: Only PNG, JPG, JPEG, GIF allowed
2. **File Size Limit**: Maximum 16MB per file
3. **Unique Constraint**: One photo per entity (student/teacher)
4. **Authentication**: All endpoints require login
5. **Binary Storage**: Photos stored as BYTEA/BLOB in database

## Performance Considerations

1. **Direct Database Storage**: Photos stored in PostgreSQL/SQLite
2. **No File System**: Eliminates file system overhead
3. **Automatic Cleanup**: Old photos replaced when new ones uploaded
4. **Efficient Retrieval**: Direct binary data streaming

## Error Handling

### Common Errors
- `Invalid file type` - File is not PNG, JPG, JPEG, or GIF
- `File too large` - File exceeds 16MB limit
- `No file selected` - Upload form submitted without file
- `Entity not found` - Student/Teacher ID doesn't exist

## Future Enhancements

1. Image compression before storage
2. Multiple photos per entity
3. Photo gallery view
4. Batch photo upload
5. Photo cropping/editing
6. Thumbnail generation
7. Photo versioning/history

## Testing

### Test Upload
```bash
# Create test image
convert -size 100x100 xc:blue test.jpg

# Upload
curl -X POST -F "photo=@test.jpg" \
  http://localhost:8000/upload_photo/student/test_id
```

### Test Retrieval
```bash
curl http://localhost:8000/get_photo/student/test_id > retrieved.jpg
```

### Test Deletion
```bash
curl -X POST http://localhost:8000/delete_photo/student/test_id
```

## Troubleshooting

### Photos Not Saving
- Check PostgreSQL/SQLite connection
- Verify database permissions
- Check file size limits
- Verify MIME type support

### Photos Not Displaying
- Check entity_type and entity_id
- Verify photo exists in database
- Check MIME type configuration
- Verify browser image support

### Upload Failures
- Check file format
- Verify file size < 16MB
- Check authentication
- Verify entity exists

# Performance Optimization Guide

## Issues Found & Fixed

### 1. **Login Slow - Admin Lookup Problem**
**Problem:** `Admin.find_by_username()` করছিল 2টি database queries
- প্রথমে `query_db()` 
- তারপর fallback এ সব admins load করে manual search

**Solution:** Direct single query use করুন
```python
@staticmethod
def find_by_username(username):
    admins = query_db('admin', username=username)
    if admins and len(admins) > 0:
        return Admin(admins[0])
    return None
```

### 2. **Add Student Page Slow**
**Problem:** প্রতিবার page load এ সব classes database থেকে fetch হচ্ছে

**Solution:** Classes list cache করুন (5 minutes)
```python
cache_key = 'classes_list_all'
classes = get_cache(cache_key)
if classes is None:
    classes = get_from_db('class')
    set_cache(cache_key, classes)
```

### 3. **Cache Invalidation Too Aggressive**
**Problem:** প্রতিটি save/update এ `clear_cache()` সব cache clear করছে

**Solution:** শুধু specific collection cache clear করুন
```python
# Old (BAD)
clear_cache(collection)  # Clears ALL cache

# New (GOOD)
keys_to_remove = [k for k in cache.keys() if k.startswith(f"cache_{collection}")]
for key in keys_to_remove:
    del cache[key]
```

### 4. **Students/Classes/Teachers Pages - Repeated Queries**
**Problem:** প্রতিবার page load এ সব data fresh fetch হচ্ছে

**Solution:** Cache করুন:
- `classes_list_all` - 5 minutes
- `teachers_list_active` - 5 minutes
- `students_list_active` - 5 minutes

## Implementation Steps

### Step 1: Update Cache Functions
Replace `clear_cache()` calls with selective clearing:

```python
def clear_collection_cache(collection):
    """Clear only specific collection cache"""
    keys_to_remove = [k for k in cache.keys() if k.startswith(f"cache_{collection}")]
    for key in keys_to_remove:
        del cache[key]
```

### Step 2: Update All Routes
Apply caching pattern to these routes:
- `/add_student` - Cache classes
- `/students` - Cache classes
- `/classes` - Cache classes & teachers
- `/teachers` - Cache teachers
- `/add_class` - Cache teachers
- `/add_teacher` - Clear teachers cache after save

### Step 3: Update Database Functions
```python
def save_to_db(collection, data):
    # ... save logic ...
    # Only clear specific collection cache
    keys_to_remove = [k for k in cache.keys() if k.startswith(f"cache_{collection}")]
    for key in keys_to_remove:
        del cache[key]
    return data_id

def update_in_db(collection, data_id, data):
    # ... update logic ...
    # Only clear specific collection cache
    keys_to_remove = [k for k in cache.keys() if k.startswith(f"cache_{collection}")]
    for key in keys_to_remove:
        del cache[key]
    return True

def delete_from_db(collection, data_id):
    # ... delete logic ...
    if cursor.rowcount > 0:
        # Only clear specific collection cache
        keys_to_remove = [k for k in cache.keys() if k.startswith(f"cache_{collection}")]
        for key in keys_to_remove:
            del cache[key]
        return True
    return False
```

## Expected Performance Improvements

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Login | 2-3 seconds | 500ms | 4-6x faster |
| Add Student Page Load | 1.5-2 seconds | 300ms | 5-7x faster |
| Students List | 2-3 seconds | 400ms | 5-7x faster |
| Classes Page | 1.5-2 seconds | 300ms | 5-7x faster |
| Teachers Page | 1-1.5 seconds | 200ms | 5-7x faster |

## Cache Timeout Settings

Current: 600 seconds (10 minutes)

Recommended:
- Static data (classes, teachers): 600s (10 min)
- Dynamic data (students, fees): 300s (5 min)
- Real-time data (attendance): 60s (1 min)

## Monitoring

Add this to check cache hit rate:
```python
@app.route('/debug/cache-stats')
@login_required
@admin_required
def cache_stats():
    return jsonify({
        'cache_size': len(cache),
        'cache_keys': list(cache.keys()),
        'cache_timeout': cache_timeout
    })
```

## Testing

After implementing changes:
1. Clear browser cache (Ctrl+Shift+Delete)
2. Test login - should be instant
3. Test add student - should load classes instantly
4. Test students list - should load instantly
5. Monitor network tab in DevTools

## Additional Optimizations (Future)

1. **Database Indexing**
   - Add index on `collection` column
   - Add composite index on `(collection, id)`

2. **Lazy Loading**
   - Load student photos only when needed
   - Paginate large lists

3. **API Endpoints**
   - Create `/api/classes` endpoint for AJAX
   - Create `/api/teachers` endpoint for AJAX

4. **Frontend Optimization**
   - Minify CSS/JS
   - Enable gzip compression (already done)
   - Use service workers for offline support

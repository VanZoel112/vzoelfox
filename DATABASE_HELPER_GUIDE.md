# Database Helper Quick Reference Guide

## 📍 Location
`/data/data/com.termux/files/home/vzoelfox/database.py`

## 🚀 Quick Import (For client.py, main.py, plugins)

```python
# Basic operations
from database import create_table, insert, select, update, delete

# Configuration management
from database import get_config, set_config, get_owner_id, get_log_channel_id

# Full database manager
from database import db_manager, config_manager
```

## 🎯 Common Usage Patterns

### For client.py
```python
# Configuration
owner_id = get_owner_id()
log_channel = get_log_channel_id()
debug_mode = get_config('debug_mode', False)

# Plugin status tracking
insert('plugin_status', {
    'plugin_name': 'example_plugin',
    'version': '1.0.0',
    'status': 'active'
})

# User session management
insert('user_sessions', {
    'user_id': event.sender_id,
    'session_start': datetime.now().isoformat()
})
```

### For main.py  
```python
# Application logging
create_table('app_logs', '''
    id INTEGER PRIMARY KEY,
    level TEXT,
    message TEXT,
    timestamp TEXT
''')

insert('app_logs', {
    'level': 'INFO',
    'message': 'Bot started',
    'timestamp': datetime.now().isoformat()
})

# Statistics tracking
update('bot_stats', {'uptime': uptime_seconds}, 'stat_name = ?', ('uptime',))
```

### For Plugins
```python
# Plugin-specific tables
create_table('my_plugin_data', '''
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
''')

# Save plugin data
insert('my_plugin_data', {
    'user_id': user_id,
    'data': json.dumps(plugin_data)
})

# Get plugin data
user_data = select('my_plugin_data', where='user_id = ?', where_params=(user_id,))
```

## 🗃️ Database Files

### Main Databases
- `vzoel_assistant.db` - Bot config, gcast history, emoji mappings
- `data/main.db` - General application data, logs
- `plugins/*.db` - Plugin-specific databases

### Automatic Database Routing
```python
# Goes to vzoel_assistant.db
insert('bot_config', data, 'vzoel_assistant')

# Goes to data/main.db  
insert('app_logs', data, 'main')

# Goes to plugins/plugin_name.db
insert('plugin_data', data, 'plugin_name')
```

## ⚙️ Configuration Management

```python
# Owner management
owner_id = get_owner_id()  # Gets from env OWNER_ID or database
set_owner_id(1234567890)   # Updates database (backup method)

# Channel configuration  
log_channel = get_log_channel_id()    # Gets from database
set_log_channel_id(-1001234567890)    # Updates database

# Custom configuration
debug = get_config('debug_mode', False, 'boolean')
set_config('bot_name', 'VzoelFox Assistant', 'string')
set_config('max_retries', 3, 'integer')
```

## 🔧 Advanced Usage

### Context Manager (Manual)
```python
from database import db_manager

with db_manager.get_connection('main') as conn:
    cursor = conn.execute('SELECT * FROM custom_table')
    results = cursor.fetchall()
```

### Backup Operations
```python
# Create backup
backup_path = db_manager.backup_database('main')
print(f"Backup created: {backup_path}")
```

### Batch Operations
```python
# Multiple inserts
for item in bulk_data:
    insert('bulk_table', item)

# Or use execute_query for custom SQL
from database import execute_query
execute_query('INSERT INTO bulk_table (data) VALUES (?)', (data,))
```

## ✅ Benefits

### No More Manual SQLite3
- ❌ `conn = sqlite3.connect('db.db')`  
- ❌ `conn.execute(sql)`
- ❌ `conn.commit()`
- ❌ `conn.close()`

### Simple Database Operations
- ✅ `insert('table', data)`
- ✅ `select('table', where='id = ?', where_params=(123,))`
- ✅ `update('table', {'status': 'active'}, 'id = ?', (123,))`

### Built-in Configuration
- ✅ `get_owner_id()` - Environment + database fallback
- ✅ `get_log_channel_id()` - Persistent channel config
- ✅ `get_config(key, default)` - Universal config storage

### Error Handling
- ✅ Automatic connection cleanup
- ✅ Transaction management
- ✅ Proper exception handling
- ✅ Logging integration

## 🎯 Ready-to-Use Examples

### Client.py Integration
```python
from database import get_owner_id, get_config, insert

async def is_owner(user_id):
    owner = get_owner_id()  # Gets from OWNER_ID env or database
    return user_id == owner

async def log_command(event, command):
    insert('command_logs', {
        'user_id': event.sender_id,
        'command': command,
        'timestamp': datetime.now().isoformat()
    })
```

### Plugin Template
```python
from database import create_table, insert, select

def setup(client):
    # Initialize plugin database
    create_table('my_plugin', '''
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        settings TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ''', 'my_plugin')  # Creates plugins/my_plugin.db
    
    @client.on(events.NewMessage(pattern=r'\.mycommand'))
    async def my_handler(event):
        # Save user interaction
        insert('my_plugin', {
            'user_id': event.sender_id,
            'settings': json.dumps({'action': 'command_used'})
        }, 'my_plugin')
```

---

**🔥 Database Helper is Ready! No more manual database code needed!** 🚀
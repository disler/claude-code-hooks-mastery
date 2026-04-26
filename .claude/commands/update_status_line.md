---
description: Upsert a key-value pair in the extras object of a session status line data file
allowed-tools: Bash, Read, Write
argument-hint: [session_id] [key] [value]
---

# Update Status Line Data

## Purpose

Update or add custom key-value pairs to a session's status line data, enabling dynamic status line customization with arbitrary metadata.

## Variables

- `session_id` - The unique session identifier to update
- `key` - The key name to upsert in the extras object
- `value` - The value to set for the specified key

## Instructions

Update the session JSON file at `.claude/data/sessions/{session_id}.json` by:
1. Locating the correct session file based on the provided session_id
2. Loading the existing JSON data
3. Creating an "extras" object if it doesn't exist
4. Upserting the key-value pair (update if exists, add if new)
5. Saving the updated JSON back to the file

## Workflow

1. Parse the session_id from $ARGUMENTS (format: "session_id key value")
2. Verify the session file exists at `.claude/data/sessions/{session_id}.json`
3. Read the current session data
4. Initialize "extras" object if not present
5. Set extras[key] = value
6. Write the updated JSON back with proper formatting
7. Confirm the update was successful

## Report

Report the following:
- Session ID that was updated
- Key that was modified
- Previous value (if it existed)
- New value that was set
- Full path to the updated session file

Example usage:
```
/update_status_line 4c932bd7-ee06-46e3-b26b-f32f52cc0862 project myapp
/update_status_line 4c932bd7-ee06-46e3-b26b-f32f52cc0862 status debugging
```
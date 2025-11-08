with open('gold_standard_enhanced_handler.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Add debug right when function is called
    if 'def enrich_gold_standard_enhanced' in line:
        # Add debug at start of function
        new_lines.append('    print(f"DEBUG HANDLER: title={title[:60]}, content_len={len(content_text)}, first_200={content_text[:200]}")\n')

with open('gold_standard_enhanced_handler.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Added debug to handler")

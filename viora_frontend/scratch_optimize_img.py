import re

with open('src/App.vue', 'r') as f:
    content = f.read()

# We only want to add loading="lazy" decoding="async" to <img> tags that don't have them
def replace_img(match):
    img_tag = match.group(0)
    if 'loading=' not in img_tag:
        # Avoid the very first hero image if possible, but for simplicity let's add to all
        # Wait, the hero image is usually near the top. We can just add it to all images that have v-for or are in grids
        img_tag = img_tag.replace('<img ', '<img loading="lazy" decoding="async" ')
    return img_tag

# Regex to match <img ... >
new_content = re.sub(r'<img [^>]+>', replace_img, content)

with open('src/App.vue', 'w') as f:
    f.write(new_content)

print("Images optimized!")

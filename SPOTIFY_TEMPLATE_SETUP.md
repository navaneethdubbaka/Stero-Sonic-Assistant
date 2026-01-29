# Spotify Play Button Template Setup

This guide explains how to use a custom template image for Spotify play button detection.

## Quick Setup

### Option 1: Use Template Matching (Most Accurate)

1. **Take a screenshot of the Spotify play button:**
   - Open Spotify and search for any song
   - Take a screenshot of just the green circular play button
   - Crop the image to include only the play button (ideally ~50x50 to ~100x100 pixels)
   - Save it as PNG format

2. **Save the image:**
   ```
   E:\Stero Sonic Assistant\assets\spotify_play_button.png
   ```

3. **Update the code:**
   Open `backend\core\tools.py` and find this line:
   ```python
   spotify_service = get_spotify_service(play_button_image_path=None)
   ```

   Change it to:
   ```python
   spotify_service = get_spotify_service(play_button_image_path="E:/Stero Sonic Assistant/assets/spotify_play_button.png")
   ```

4. **Restart the application**

### Option 2: Use Color Detection (Default - No Setup Required)

The system will automatically use color detection to find green circular buttons if no template image is provided.

## How Template Matching Works

1. **Takes a screenshot** of the entire screen
2. **Searches for your template image** at multiple scales (50% to 150%)
3. **Finds the best match** with >60% confidence
4. **Clicks on the center** of the matched button

## Tips for Best Results

### For Template Image:
- ✅ Crop tightly around the play button
- ✅ Use PNG format with transparent background (optional)
- ✅ Button should be clearly visible and not blurred
- ✅ Size: 50x50 to 100x100 pixels works best
- ❌ Don't include text or other UI elements
- ❌ Don't make it too small (<30px) or too large (>150px)

### Example Template Image:
```
[Green circular button with white play triangle in center]
```

## Fallback Behavior

The system has multiple fallback levels:
1. **Template Matching** (if image provided) - Most accurate
2. **Color Detection** (green circular shapes) - Automatic fallback
3. **Keyboard Navigation** (Tab + Enter + Space) - Last resort

## Troubleshooting

### Template matching not working?
- Check the image path is correct
- Verify the image exists at the specified location
- Try taking a new screenshot at different scale
- Check console logs for confidence percentage

### Color detection not finding button?
- Make sure Spotify is visible on screen
- Button should be clearly visible (not hidden/scrolled off)
- Adjust the green color range in code if needed

## Advanced: Custom Color Ranges

If you want to adjust color detection, edit `spotify_service.py`:

```python
# Current green range (works for Spotify)
lower_green = np.array([35, 100, 100])  # HSV lower bound
upper_green = np.array([85, 255, 255])  # HSV upper bound
```

## Example Code

```python
# In backend/core/tools.py

# Option 1: Use template matching
spotify_service = get_spotify_service(
    play_button_image_path="E:/Stero Sonic Assistant/assets/spotify_play_button.png"
)

# Option 2: Use color detection (default)
spotify_service = get_spotify_service(play_button_image_path=None)

# Option 3: Use custom template location
spotify_service = get_spotify_service(
    play_button_image_path="C:/Users/YourName/Desktop/my_play_button.png"
)
```

import cv2 as cv
from wwm.window import Window

#template_name = "template_buddhas_tear.png"
template_name = "template_jade_tower_peony.png"
#template_name = "template_waypoint.png"

threshold = 0.6

# Take a screenshot
window = Window()
img_rgb = window.get_screenshot()
assert img_rgb is not None, "Screenshot could not be captured."

coords, _ = window.get_coords_template_match(template_name, threshold=threshold)
for x, y in coords:
    cv.circle(img_rgb, (x, y), radius=16, color=(0, 0, 255), thickness=2)

cv.imshow("Template Match Result", img_rgb)
cv.waitKey(0)  # Wait until any key is pressed
cv.destroyAllWindows()

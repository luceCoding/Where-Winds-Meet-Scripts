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
center_x = _.shape[1] // 2
center_y = _.shape[0] // 2
print(center_x, center_y)
# Sort all waypoint coords by distance to the center of the window
coords_sorted = sorted(
    coords,
    key=lambda p: (p[0] - center_x) ** 2 + (p[1] - center_y) ** 2
)
for x, y in coords_sorted:
    cv.circle(img_rgb, (x, y), radius=16, color=(0, 0, 255), thickness=2)

cv.imshow("Template Match Result", img_rgb)
cv.waitKey(0)  # Wait until any key is pressed
cv.destroyAllWindows()

import cv2
import numpy as np


def preprocess_image(image):
    """Preprocess the image for contour detection."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    kernel = np.ones((3, 3), np.uint8)
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    return morph


def find_column_contours(preprocessed_image, min_area=10000, max_contours=10):
    """Find and filter contours to identify potential columns."""
    contours, _ = cv2.findContours(preprocessed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:max_contours]

    column_boxes = []
    for contour in contours:
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if 4 <= len(approx) <= 6 and cv2.contourArea(approx) > min_area:  # Allow for some flexibility in shape
            rect = cv2.minAreaRect(approx)
            box = cv2.boxPoints(rect)
            box = np.int32(box)
            column_boxes.append(box)

    return column_boxes


def perspective_transform(image, src_pts):
    """Apply perspective transform to a set of points."""
    src_pts = src_pts.reshape(4, 2).astype(np.float32)
    src_pts = src_pts[np.argsort(src_pts[:, 1])]
    top_pts = src_pts[:2][np.argsort(src_pts[:2, 0])]
    bottom_pts = src_pts[2:][np.argsort(src_pts[2:, 0])]
    src_pts = np.concatenate((top_pts, bottom_pts[::-1]))

    width = int(max(np.linalg.norm(src_pts[0] - src_pts[1]),
                    np.linalg.norm(src_pts[2] - src_pts[3])))
    height = int(max(np.linalg.norm(src_pts[0] - src_pts[3]),
                     np.linalg.norm(src_pts[1] - src_pts[2])))

    dst_pts = np.array([[0, 0], [width - 1, 0],
                        [width - 1, height - 1], [0, height - 1]], dtype=np.float32)

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    return cv2.warpPerspective(image, M, (width, height))


def order_boxes(boxes, image_width):
    """Order boxes based on their column and vertical position."""
    col_width = image_width // 3

    box_info = []
    for i, box in enumerate(boxes):
        x = np.mean(box[:, 0])
        y = np.mean(box[:, 1])
        col = int(x // col_width)
        box_info.append((i, col, y, box))

    sorted_boxes = sorted(box_info, key=lambda x: (x[1], x[2]))

    final_order = []
    col_counts = [0, 0, 0]
    for _, col, _, box in sorted_boxes:
        if col == 0 and col_counts[0] < 4:
            final_order.append(box)
            col_counts[0] += 1
        elif col in [1, 2] and col_counts[col] < 1:
            final_order.append(box)
            col_counts[col] += 1

    return final_order


def multi_column_correction(image, min_area=10000, max_contours=10, visualize=True):
    """
    Correct perspective and extract columns from an exam paper image.

    Args:
    image (numpy.ndarray): Input image
    min_area (int): Minimum contour area to consider as a column
    max_contours (int): Maximum number of contours to process
    visualize (bool): Whether to create a visualization image

    Returns:
    tuple: (list of corrected column images, visualization image if visualize=True else None)
    """
    preprocessed = preprocess_image(image)
    column_boxes = find_column_contours(preprocessed, min_area, max_contours)

    ordered_boxes = order_boxes(column_boxes, image.shape[1])

    corrected_columns = [perspective_transform(image, box) for box in ordered_boxes]

    if visualize:
        vis_image = image.copy()
        for i, box in enumerate(ordered_boxes):
            cv2.drawContours(vis_image, [box], 0, (0, 255, 0), 2)
            x, y = box[0]
            cv2.putText(vis_image, str(i + 1), (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        return corrected_columns, vis_image
    else:
        return corrected_columns


# Example usage
if __name__ == "__main__":
    image_path = "./target/3.jpg"
    image = cv2.imread(image_path)

    result = multi_column_correction(image, min_area=10000, max_contours=6, visualize=True)

    if len(result) == 2:
        corrected_columns, vis_image = result
        cv2.imwrite("detected_columns_ordered.jpg", vis_image)
    else:
        corrected_columns = result

    for i, column in enumerate(corrected_columns):
        cv2.imwrite(f"corrected_column_{i + 1}.jpg", column)
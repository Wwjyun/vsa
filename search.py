from vsa_paths import map_image_path


def perform_search(option, number, code, button_name):
    return str(map_image_path(option, number, button_name, code))

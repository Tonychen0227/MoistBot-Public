ScreenType_YComms = 1
ScreenType_PendingConfirmation = 2
ScreenType_BoxView = 3
ScreenType_Warning = 4
ScreenType_SoftBan = 5


def is_correct_screen(bytes, expected_type):
    if str(bytes) == "8A79FFFF":
        return expected_type == ScreenType_YComms
    elif str(bytes) == "83B400FF":
        return expected_type == ScreenType_PendingConfirmation
    elif str(bytes) == "9BD500FF":
        return expected_type == ScreenType_BoxView
    elif str(bytes) == "5E8300BF":
        return expected_type == ScreenType_Warning
    elif str(bytes) == "000000FF":
        return expected_type == ScreenType_SoftBan
    else:
        return False

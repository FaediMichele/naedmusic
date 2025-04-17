
from android.permissions import request_permissions, Permission, check_permission # type: ignore
from jnius import autoclass, PythonJavaClass, java_method, cast # type:ignore
from kivy.logger import Logger
from android import activity as AndroidActivity

Intent = autoclass('android.content.Intent')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Consumer = autoclass('java.util.function.Consumer')

PlaybackService = autoclass('org.test.naedmusic.PlaybackService')
PlayerControllerContainer = autoclass('org.test.naedmusic.PlayerControllerContainer')
PlaybackService.startService(PythonActivity.mActivity)
mplayer_controller_container = PlayerControllerContainer(PythonActivity.mActivity.getApplicationContext())
MediaRepository = autoclass('org.test.naedmusic.MediaRepository')

class MyBiFunction(PythonJavaClass):
    __javainterfaces__ = (
        'java.util.function.Consumer', )

    def __init__(self, callback):
        super(MyBiFunction, self).__init__()
        self.callback = callback

    @java_method('(Ljava/lang/Object;)V')
    def accept(self, container):

        self.callback(container.context, container.intent)

def save_external_file(filename, content):
    currentActivity = PythonActivity.mActivity

    intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType("application/json")
    intent.putExtra(Intent.EXTRA_TITLE, filename)
    my_request_code = 42

    def on_activity_result(request_code, result_code, intent):
        if request_code == my_request_code:
            if result_code == -1:
                uri = intent.getData()
                try:
                    parcelFileDescriptor = currentActivity.getContentResolver().openFileDescriptor(uri, "w")
                    fileOutputStream = parcelFileDescriptor.getFileDescriptor()
                    stream = autoclass('java.io.FileOutputStream')(fileOutputStream)
                    stream.write(content.encode('utf-8'))
                    stream.close()
                    parcelFileDescriptor.close()
                except Exception as e:
                    Logger.debug("Error writing file", e)
            else:
                Logger.debug("Error Activity ", result_code)

    AndroidActivity.bind(on_activity_result=on_activity_result)

    PythonActivity.onActivityResult = on_activity_result
    currentActivity.startActivityForResult(intent, my_request_code)

def load_external_file(callback=lambda uri, content: None):
    currentActivity = PythonActivity.mActivity

    intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType("application/json")
    my_request_code = 43

    # onActivityResult callback
    def on_activity_result(request_code, result_code, intent):
        if request_code == my_request_code:  # Arbitrary request code
            if result_code == -1:  # RESULT_OK
                uri = intent.getData()
                try:
                    parcelFileDescriptor = currentActivity.getContentResolver().openFileDescriptor(uri, "r")
                    fileInputStream = parcelFileDescriptor.getFileDescriptor()

                    # Read your file content here
                    stream = autoclass('java.io.FileInputStream')(fileInputStream)
                    InputStreamReader = autoclass('java.io.InputStreamReader')
                    BufferedReader = autoclass('java.io.BufferedReader')
                    StringBuilder = autoclass('java.lang.StringBuilder')
                    
                    reader = BufferedReader(InputStreamReader(stream))
                    sb = StringBuilder()
                    line = reader.readLine()

                    while line is not None:
                        sb.append(line).append("\n")
                        line = reader.readLine()

                    stream.close()
                    parcelFileDescriptor.close()

                    file_content = sb.toString()
                    callback(uri, file_content)
                except Exception as e:
                    print("Error reading file", e)

    AndroidActivity.bind(on_activity_result=on_activity_result)

    # Start the activity
    PythonActivity.onActivityResult = on_activity_result
    currentActivity.startActivityForResult(intent, my_request_code)  # Arbitrary request code
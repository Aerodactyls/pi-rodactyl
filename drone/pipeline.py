import globals
from log import log
import depthai


def createPipeline() -> None:
    if globals.pipeline is not None:
        raise RuntimeError("Pipeline already exists. Cannot create a new one.")

    log("Creating Pipeline")

    globals.pipeline = depthai.Pipeline()
    cam_rgb = globals.pipeline.createColorCamera()
    cam_rgb.setPreviewSize(globals.VIDEO_RESOLUTION, globals.VIDEO_RESOLUTION)
    cam_rgb.setInterleaved(False)
    xout_rgb = globals.pipeline.createXLinkOut()
    xout_rgb.setStreamName("rgb")
    cam_rgb.preview.link(xout_rgb.input)

    controlIn = globals.pipeline.create(depthai.node.XLinkIn)
    controlIn.setStreamName("control")
    controlIn.out.link(cam_rgb.inputControl)

    log("Pipeline created sucessfully")

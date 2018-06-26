import base64
from io import BytesIO as _BytesIO
import time

import dash_core_components as dcc
import dash_html_components as html
import numpy as np

import plotly.graph_objs as go
from PIL import Image


# Variables
HTML_IMG_SRC_PARAMETERS = 'data:image/png;base64, '


# Display utility functions
def _merge(a, b):
    return dict(a, **b)


def _omit(omitted_keys, d):
    return {k: v for k, v in d.items() if k not in omitted_keys}


# Image utility functions
def pil_to_b64(im, enc_format='png', verbose=False):
    """
    Converts a PIL Image into base64 string for HTML displaying
    :param im: PIL Image object
    :param enc_format: The image format for displaying. If saved the image will have that extension.
    :return: base64 encoding
    """
    t_start = time.time()

    buff = _BytesIO()
    if enc_format == 'png':
        im.save(buff, format=enc_format, compress_level=1)
    elif enc_format == 'jpeg':
        im.save(buff, format=enc_format, quality=95)
    else:
        im.save(buff, format=enc_format)
    encoded = base64.b64encode(buff.getvalue()).decode("utf-8")

    t_end = time.time()
    if verbose:
        print(f"PIL converted to b64 in {t_end - t_start:.3f} sec")

    return encoded


def numpy_to_b64(np_array, enc_format='png', scalar=True):
    """
    Converts a numpy image into base 64 string for HTML displaying
    :param np_array:
    :param enc_format: The image format for displaying. If saved the image will have that extension.
    :param scalar:
    :return:
    """
    # Convert from 0-1 to 0-255
    if scalar:
        np_array = np.uint8(255 * np_array)
    else:
        np_array = np.uint8(np_array)

    im_pil = Image.fromarray(np_array)

    return pil_to_b64(im_pil, enc_format)


def b64_to_pil(string):
    decoded = base64.b64decode(string)
    buffer = _BytesIO(decoded)
    im = Image.open(buffer)

    return im


def b64_to_numpy(string, to_scalar=True):
    im = b64_to_pil(string)
    np_array = np.asarray(im)

    if to_scalar:
        np_array = np_array / 255.

    return np_array


def pil_to_bytes_string(im):
    """
    Converts a PIL Image object into the ASCII string representation of its bytes. This is only recommended for
    its speed, and takes more space than any encoding. The following are sample results ran on a 3356 x 2412
    jpg image:
    (to be added)

    Here is the time taken to save the image as a png inside a buffer (BytesIO):
        Time taken to convert from b64 to PIL:
        30.6 ms ± 3.58 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)

        Time taken to convert from PIL to b64:
        1.77 s ± 66.1 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

    Note that it CANNOT be displayed in html img tags.

    :param im:
    :return: The encoded string, and the size of the original image
    """
    size = im.size
    mode = im.mode
    im_bytes = im.tobytes()
    encoding_string = base64.b64encode(im_bytes).decode('ascii')

    return encoding_string, size, mode


def bytes_string_to_pil(encoding_string, size, mode='RGB'):
    """
    Converts the ASCII string representation of a PIL Image bytes into the original PIL Image object. This
    function is only recommended for its speed, and takes more space than any encoding. The following are
    sample results ran on a 3356 x 2412 jpg image:
    (to be added)

    Here is the time taken to save the image as a png inside a buffer (BytesIO), then encode into b64:

        Time taken to convert from b64 to PIL:
        30.6 ms ± 3.58 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)

        Time taken to convert from PIL to b64:
        1.77 s ± 66.1 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

    Note that it CANNOT be displayed in html img tags.

    :param encoding_string:
    :param size:
    :param mode:
    :return:
    """
    if type(size) is str:
        size = eval(size)

    if type(size) not in [tuple, list]:
        raise ValueError("Incorrect Size type when trying to convert from bytes to PIL Image.")

    encoding_bytes = encoding_string.encode('ascii')
    decoded = base64.b64decode(encoding_bytes)

    im = Image.frombytes(mode, size, decoded)

    return im


# Custom Display Components
def Card(children, **kwargs):
    return html.Section(
        children,
        style=_merge({
            'padding': 20,
            'margin': 5,
            'borderRadius': 5,
            'border': 'thin lightgrey solid',

            # Remove possibility to select the text for better UX
            'user-select': 'none',
            '-moz-user-select': 'none',
            '-webkit-user-select': 'none',
            '-ms-user-select': 'none'
        }, kwargs.get('style', {})),
        **_omit(['style'], kwargs)
    )


def NamedSlider(name, short, min, max, step, val, marks=None):
    if marks:
        step = None
    else:
        marks = {i: i for i in range(min, max + 1, step)}

    return html.Div(
        style={'margin': '25px 5px 30px 0px'},
        children=[
            f"{name}:",

            html.Div(
                style={'margin-left': '5px'},
                children=dcc.Slider(
                    id=f'slider-{short}',
                    min=min,
                    max=max,
                    marks=marks,
                    step=step,
                    value=val
                )
            )
        ]
    )


def NamedInlineRadioItems(name, short, options, val, **kwargs):
    return html.Div(
        id=f'div-{short}',
        style=_merge({
            'display': 'inline-block'
        }, kwargs.get('style', {})),
        children=[
            f'{name}:',
            dcc.RadioItems(
                id=f'radio-{short}',
                options=options,
                value=val,
                labelStyle={
                    'display': 'inline-block',
                    'margin-right': '7px',
                    'font-weight': 300
                },
                style={
                    'display': 'inline-block',
                    'margin-left': '7px'
                }
            )
        ],
        **_omit(['style'], kwargs)
    )


# Custom Image Components
def InteractiveImagePIL(image_id, image, enc_format='png', display_mode='scalable', verbose=False, **kwargs):
    encoded_image = pil_to_b64(image, enc_format=enc_format, verbose=verbose)

    width, height = image.size

    if display_mode.lower() in ['scalable', 'scale']:
        display_height = '{}vw'.format(round(60 * height / width))
    else:
        display_height = '75vh'

    return dcc.Graph(
        id=image_id,
        figure={
            'data': [],
            'layout': {
                'margin': go.Margin(l=40, b=40, t=26, r=10),
                'xaxis': {
                    'range': (0, width),
                    'scaleanchor': 'y',
                    'scaleratio': 1
                },
                'yaxis': {
                    'range': (0, height)
                },
                'images': [{
                    'xref': 'x',
                    'yref': 'y',
                    'x': 0,
                    'y': 0,
                    'yanchor': 'bottom',
                    'sizing': 'stretch',
                    'sizex': width,
                    'sizey': height,
                    'layer': 'below',
                    'source': HTML_IMG_SRC_PARAMETERS + encoded_image,
                }],
                'dragmode': 'select',
            }
        },
        style=_merge({
            'height': display_height,
            'width': '100%'
        }, kwargs.get('style', {})),

        config={
            'modeBarButtonsToRemove': [
                'sendDataToCloud',
                'autoScale2d',
                'toggleSpikelines',
                'hoverClosestCartesian',
                'hoverCompareCartesian',
                'zoom2d'
            ]
        },

        **_omit(['style'], kwargs)
    )


def DisplayImagePIL(id, image, **kwargs):
    encoded_image = pil_to_b64(image, enc_format='png')

    return html.Img(
        id=f'img-{id}',
        src=HTML_IMG_SRC_PARAMETERS + encoded_image,
        width='100%',
        **kwargs
    )


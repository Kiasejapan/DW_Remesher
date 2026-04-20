# -*- coding: utf-8 -*-
"""
DW_Remesher.py
Cylinder cleanup / resides tool for Maya 2018-2025
Python 2.7 / 3.x compatible
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import math

# Version is rewritten by build.py at every build
# Format: YYYY.MM.DD.HHMM
VERSION = "2026.04.20.1238"

# GitHub raw file URL for auto-update
_GITHUB_RAW_URL = "https://raw.githubusercontent.com/Kiasejapan/DW_Remesher/main/DW_Remesher.py"

PY2 = sys.version_info[0] == 2

# Python 2/3 compatible reload
if PY2:
    _reload = reload   # noqa: F821  (builtin in Py2)
else:
    import importlib
    _reload = importlib.reload

try:
    import maya.cmds as cmds
    import maya.OpenMaya as om
    import maya.OpenMayaUI as omui
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance
except ImportError:
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        from shiboken6 import wrapInstance
    except ImportError:
        from PySide import QtWidgets, QtCore, QtGui
        from shiboken import wrapInstance


# ---------------------------------------------------------------------------
# Localization
# ---------------------------------------------------------------------------
LANG_EN = "en"
LANG_JP = "jp"
_current_lang = LANG_EN
_saved_geometry = None
_saved_lang = None

_STRINGS = {
    # ---- Window / common ---------------------------------------------
    "window_title":         {"en": "DW Remesher",
                             "jp": u"DW \u30ea\u30e1\u30c3\u30b7\u30e3\u30fc"},
    "btn_reload":           {"en": "Reload",                        "jp": u"\u30ea\u30ed\u30fc\u30c9"},
    "btn_update":           {"en": "Check for Updates",             "jp": u"\u66f4\u65b0\u3092\u78ba\u8a8d"},
    "btn_help":             {"en": "?",                             "jp": u"?"},
    "btn_lang":             {"en": "JP",                            "jp": u"EN"},
    "btn_close":            {"en": "Close",                         "jp": u"\u9589\u3058\u308b"},
    "btn_set":              {"en": "Set",                           "jp": u"\u30bb\u30c3\u30c8"},
    "status_ready":         {"en": "Ready",                         "jp": u"\u6e96\u5099\u5b8c\u4e86"},

    # ---- Tabs --------------------------------------------------------
    "tab_cylinder":         {"en": "Cylinder",                      "jp": u"\u5186\u67f1"},

    # ---- Cylinder Cleanup (cc_*) -------------------------------------
    "cc_grp_title":         {"en": "Cylinder Cleanup",
                             "jp": u"\u5186\u67f1\u30af\u30ea\u30fc\u30f3\u30a2\u30c3\u30d7"},
    "cc_lbl_target":        {"en": "Target:",                       "jp": u"\u5bfe\u8c61:"},
    "cc_lbl_axis":          {"en": "Axis:",                         "jp": u"\u8ef8:"},
    "cc_ax_auto":           {"en": "Auto",                          "jp": u"\u81ea\u52d5"},
    "cc_lbl_mode":          {"en": "Mode:",                         "jp": u"\u30e2\u30fc\u30c9:"},
    "cc_mode_full":         {"en": "Round && Straighten",
                             "jp": u"\u6574\u5217\uff0b\u5747\u7b49\u5316"},
    "cc_mode_radius":       {"en": "Radius only",
                             "jp": u"\u534a\u5f84\u306e\u307f"},
    "cc_lbl_radius_avg":    {"en": "Radius policy:",
                             "jp": u"\u534a\u5f84\u306e\u6c7a\u3081\u65b9:"},
    "cc_radius_mean":       {"en": "Mean",                          "jp": u"\u5e73\u5747"},
    "cc_radius_median":     {"en": "Median",                        "jp": u"\u4e2d\u592e\u5024"},
    "cc_btn_apply":         {"en": "Cleanup",                       "jp": u"\u6574\u5f62"},
    "cc_info_detected":     {"en": "Axis: {axis}  Rings: {rings}  Sides: {sides}",
                             "jp": u"\u8ef8: {axis}  \u30ea\u30f3\u30b0\u6570: {rings}  \u89d2\u6570: {sides}"},

    # ---- Change Sides / Resides (rs_*) -------------------------------
    "rs_grp_title":         {"en": "Change Sides (N\u21C4M)",
                             "jp": u"\u89d2\u6570\u5909\u66f4 (N\u21C4M)"},
    "rs_lbl_target":        {"en": "Target:",                       "jp": u"\u5bfe\u8c61:"},
    "rs_lbl_current":       {"en": "Current sides:",                "jp": u"\u73fe\u5728\u306e\u89d2\u6570:"},
    "rs_lbl_target_sides":  {"en": "Target sides:",                 "jp": u"\u5909\u66f4\u5f8c\u306e\u89d2\u6570:"},
    "rs_chk_keep_uv":       {"en": "Preserve UV (cylindrical projection)",
                             "jp": u"UV \u3092\u7dad\u6301 (\u5186\u7b52\u6295\u5f71)"},
    "rs_chk_keep_caps":     {"en": "Create end caps",
                             "jp": u"\u7aef\u30ad\u30e3\u30c3\u30d7\u3092\u4f5c\u6210"},
    "rs_chk_replace":       {"en": "Replace original (otherwise duplicate)",
                             "jp": u"\u5143\u3092\u7f6e\u304d\u63db\u3048\u308b (\u30aa\u30d5\u306a\u3089\u8907\u88fd)"},
    "rs_btn_apply":         {"en": "Apply",                         "jp": u"\u9069\u7528"},

    # ---- Status / Errors ---------------------------------------------
    "status_no_mesh":       {"en": "No mesh selected.",
                             "jp": u"\u30e1\u30c3\u30b7\u30e5\u304c\u9078\u629e\u3055\u308c\u3066\u3044\u307e\u305b\u3093\u3002"},
    "status_not_cyl":       {"en": "Mesh does not look like a cylinder (axis/rings undetectable).",
                             "jp": u"\u30e1\u30c3\u30b7\u30e5\u304c\u5186\u67f1\u3068\u3057\u3066\u8a8d\u8b58\u3067\u304d\u307e\u305b\u3093\u3002"},
    "status_cleanup_done":  {"en": "Cleanup done. Axis={axis}, rings={rings}, sides={sides}.",
                             "jp": u"\u6574\u5f62\u5b8c\u4e86\u3002\u8ef8={axis}, \u30ea\u30f3\u30b0={rings}, \u89d2\u6570={sides}"},
    "status_resides_done":  {"en": "Resides done: {old}-gon \u2192 {new}-gon ({rings} rings).",
                             "jp": u"\u89d2\u6570\u5909\u66f4\u5b8c\u4e86: {old}\u89d2 \u2192 {new}\u89d2 ({rings} \u30ea\u30f3\u30b0)"},
    "status_target_not_set":{"en": "Target mesh is not set.",
                             "jp": u"\u5bfe\u8c61\u30e1\u30c3\u30b7\u30e5\u304c\u672a\u8a2d\u5b9a\u3067\u3059\u3002"},
    "status_error":         {"en": "Error: {msg}",
                             "jp": u"\u30a8\u30e9\u30fc: {msg}"},
    "status_target_set":    {"en": "Target: {name}",
                             "jp": u"\u5bfe\u8c61: {name}"},

    # ---- Help --------------------------------------------------------
    "help_title":           {"en": "Help \u2014 DW Remesher",
                             "jp": u"\u30d8\u30eb\u30d7 \u2014 DW \u30ea\u30e1\u30c3\u30b7\u30e3\u30fc"},
    "help_body_cylinder": {
        "en": "<h2>Cylinder Tab</h2>"
              "<h3>Cylinder Cleanup</h3>"
              "<p>Takes a distorted cylindrical mesh and snaps it to a "
              "perfectly regular cylinder. The original topology and UVs "
              "are preserved; only vertex positions change.</p>"
              "<ol>"
              "<li>Select the mesh in the viewport and click <b>[Set]</b>.</li>"
              "<li>Choose an <b>Axis</b>:"
              "<ul>"
              "<li><b>Auto</b> \u2014 detected by principal-component analysis (PCA) of the mesh.</li>"
              "<li><b>X / Y / Z</b> \u2014 force a local axis.</li>"
              "</ul></li>"
              "<li>Choose a <b>Mode</b>:"
              "<ul>"
              "<li><b>Round &amp; Straighten</b> \u2014 equalize both radii and angular spacing (fully regular).</li>"
              "<li><b>Radius only</b> \u2014 equalize radii but keep each vertex's original angle around the axis.</li>"
              "</ul></li>"
              "<li>Pick a <b>Radius policy</b>: <b>Mean</b> (default) or <b>Median</b> (robust to outliers).</li>"
              "<li>Click <b>[Cleanup]</b>.</li>"
              "</ol>"
              "<h3>Change Sides (N\u21C4M)</h3>"
              "<p>Rebuilds the selected cylinder with a different polygon side count. "
              "Rings (edge loops along the axis) and their per-ring radii are kept. "
              "Cylindrical UV projection is applied to the new mesh.</p>"
              "<ol>"
              "<li>Select the cylinder and click <b>[Set]</b>. The current side count is auto-detected.</li>"
              "<li>Set <b>Target sides</b> (3-128).</li>"
              "<li>Toggle <b>Create end caps</b> if the source had them.</li>"
              "<li>Toggle <b>Replace original</b> to delete the source after conversion, or keep it off to create a duplicate.</li>"
              "<li>Click <b>[Apply]</b>.</li>"
              "</ol>"
              "<p><b>Note:</b> UVs are recreated by cylindrical projection, not transferred 1:1. "
              "Meshes whose original UVs were a standard cylindrical layout will look nearly identical.</p>",
        "jp": u"<h2>\u5186\u67f1\u30bf\u30d6</h2>"
              u"<h3>\u5186\u67f1\u30af\u30ea\u30fc\u30f3\u30a2\u30c3\u30d7</h3>"
              u"<p>\u6b6a\u3093\u3060\u5186\u67f1\u5f62\u30e1\u30c3\u30b7\u30e5\u3092\u3001\u5b8c\u5168\u306b\u6574\u3063\u305f\u5186\u67f1\u306b\u30b9\u30ca\u30c3\u30d7\u3057\u307e\u3059\u3002"
              u"\u30c8\u30dd\u30ed\u30b8\u3068 UV \u306f\u305d\u306e\u307e\u307e\u3001\u9802\u70b9\u4f4d\u7f6e\u3060\u3051\u304c\u5909\u308f\u308a\u307e\u3059\u3002</p>"
              u"<ol>"
              u"<li>\u30d3\u30e5\u30fc\u30dd\u30fc\u30c8\u3067\u30e1\u30c3\u30b7\u30e5\u3092\u9078\u629e\u3057\u3001<b>[\u30bb\u30c3\u30c8]</b> \u3092\u30af\u30ea\u30c3\u30af\u3002</li>"
              u"<li><b>\u8ef8</b> \u3092\u9078\u629e\uff1a"
              u"<ul>"
              u"<li><b>\u81ea\u52d5</b> \u2014 \u30e1\u30c3\u30b7\u30e5\u306e\u4e3b\u6210\u5206\u5206\u6790 (PCA) \u3067\u81ea\u52d5\u5224\u5b9a\u3002</li>"
              u"<li><b>X / Y / Z</b> \u2014 \u30ed\u30fc\u30ab\u30eb\u8ef8\u3092\u660e\u793a\u7684\u306b\u6307\u5b9a\u3002</li>"
              u"</ul></li>"
              u"<li><b>\u30e2\u30fc\u30c9</b> \u3092\u9078\u629e\uff1a"
              u"<ul>"
              u"<li><b>\u6574\u5217\uff0b\u5747\u7b49\u5316</b> \u2014 \u534a\u5f84\u3068\u89d2\u5ea6\u9593\u9694\u3092\u4e21\u65b9\u63c3\u3048\u307e\u3059\uff08\u5b8c\u5168\u306b\u898f\u5247\u7684\uff09\u3002</li>"
              u"<li><b>\u534a\u5f84\u306e\u307f</b> \u2014 \u534a\u5f84\u306f\u63c3\u3048\u3064\u3064\u3001\u5404\u9802\u70b9\u306e\u89d2\u5ea6\u306f\u7dad\u6301\u3002</li>"
              u"</ul></li>"
              u"<li><b>\u534a\u5f84\u306e\u6c7a\u3081\u65b9</b>\uff1a<b>\u5e73\u5747</b> (\u63a8\u5968) \u307e\u305f\u306f <b>\u4e2d\u592e\u5024</b> (\u5916\u308c\u5024\u306b\u5f37\u3044)\u3002</li>"
              u"<li><b>[\u6574\u5f62]</b> \u3092\u30af\u30ea\u30c3\u30af\u3002</li>"
              u"</ol>"
              u"<h3>\u89d2\u6570\u5909\u66f4 (N\u21C4M)</h3>"
              u"<p>\u9078\u629e\u5186\u67f1\u3092\u5225\u306e\u89d2\u6570\u3067\u518d\u69cb\u7bc9\u3057\u307e\u3059\u3002"
              u"\u30ea\u30f3\u30b0\uff08\u8ef8\u65b9\u5411\u306e\u30a8\u30c3\u30b8\u30eb\u30fc\u30d7\uff09\u3068\u5404\u30ea\u30f3\u30b0\u306e\u534a\u5f84\u306f\u4fdd\u6301\u3055\u308c\u307e\u3059\u3002"
              u"\u65b0\u30e1\u30c3\u30b7\u30e5\u306b\u306f\u5186\u7b52\u6295\u5f71\u306e UV \u304c\u9069\u7528\u3055\u308c\u307e\u3059\u3002</p>"
              u"<ol>"
              u"<li>\u5186\u67f1\u3092\u9078\u629e\u3057\u3066 <b>[\u30bb\u30c3\u30c8]</b>\u3002\u73fe\u5728\u306e\u89d2\u6570\u304c\u81ea\u52d5\u691c\u51fa\u3055\u308c\u307e\u3059\u3002</li>"
              u"<li><b>\u5909\u66f4\u5f8c\u306e\u89d2\u6570</b> (3\uff5e128) \u3092\u8a2d\u5b9a\u3002</li>"
              u"<li>\u5143\u30e1\u30c3\u30b7\u30e5\u306b\u7aef\u30ad\u30e3\u30c3\u30d7\u304c\u3042\u308b\u306a\u3089 <b>\u7aef\u30ad\u30e3\u30c3\u30d7\u3092\u4f5c\u6210</b> \u3092\u30aa\u30f3\u3002</li>"
              u"<li><b>\u5143\u3092\u7f6e\u304d\u63db\u3048\u308b</b>\uff1a\u30aa\u30f3\u3067\u5143\u30e1\u30c3\u30b7\u30e5\u3092\u524a\u9664\u3001\u30aa\u30d5\u3067\u8907\u88fd\u3068\u3057\u3066\u751f\u6210\u3002</li>"
              u"<li><b>[\u9069\u7528]</b> \u3092\u30af\u30ea\u30c3\u30af\u3002</li>"
              u"</ol>"
              u"<p><b>\u6ce8\u610f:</b> UV \u306f\u5186\u7b52\u6295\u5f71\u3067\u518d\u751f\u6210\u3055\u308c\u307e\u3059\uff081:1 \u3067\u306e\u8ee2\u9001\u3067\u306f\u3042\u308a\u307e\u305b\u3093\uff09\u3002"
              u"\u5143\u304c\u6a19\u6e96\u7684\u306a\u5186\u7b52 UV \u30ec\u30a4\u30a2\u30a6\u30c8\u306a\u3089\u307b\u307c\u5909\u5316\u3057\u307e\u305b\u3093\u3002</p>",
    },
}

# Python 2/3 unicode type compatibility for tr()
try:
    _TEXT_TYPE = unicode  # Python 2
except NameError:
    _TEXT_TYPE = str       # Python 3


def _to_unicode(s):
    """Force a value into unicode (Python 2) / str (Python 3).

    On Maya 2018 + Japanese Windows (CP932 locale), str.format() with
    a mix of bytes-str and unicode triggers ASCII auto-decoding which
    fails for non-ASCII characters. Returning unicode-only from tr()
    eliminates this entire class of error.
    """
    if isinstance(s, _TEXT_TYPE):
        return s
    if isinstance(s, bytes):
        try:
            return s.decode("utf-8")
        except Exception:
            return s.decode("utf-8", "replace")
    try:
        return _TEXT_TYPE(s)
    except Exception:
        return _TEXT_TYPE(repr(s))


def tr(key, **kw):
    e = _STRINGS.get(key, {})
    if isinstance(e, dict) and ("en" in e or "jp" in e):
        t = e.get(_current_lang, e.get("en", key))
    else:
        t = key
    t = _to_unicode(t)
    if kw:
        kw = {k: _to_unicode(v) for k, v in kw.items()}
        try:
            t = t.format(**kw)
        except Exception:
            pass
    return t


# ---------------------------------------------------------------------------
# Math helpers  (pure Python, no Maya dependency)
# ---------------------------------------------------------------------------
_EPS = 1e-9


def _vsub(a, b):  return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def _vadd(a, b):  return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def _vmul(a, s):  return (a[0]*s, a[1]*s, a[2]*s)
def _vdot(a, b):  return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def _vcross(a, b):
    return (a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])
def _vlen(a):     return math.sqrt(a[0]*a[0] + a[1]*a[1] + a[2]*a[2])


def _vnorm(a):
    L = _vlen(a)
    if L < _EPS:
        return (0.0, 0.0, 0.0)
    return (a[0]/L, a[1]/L, a[2]/L)


def _centroid(pts):
    if not pts:
        return (0.0, 0.0, 0.0)
    n = len(pts)
    sx = sy = sz = 0.0
    for p in pts:
        sx += p[0]; sy += p[1]; sz += p[2]
    return (sx / n, sy / n, sz / n)


def _median(values):
    """Median of a list of floats. Returns 0.0 for empty list."""
    n = len(values)
    if n == 0:
        return 0.0
    s = sorted(values)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return 0.5 * (s[mid - 1] + s[mid])


# ---------------------------------------------------------------------------
# Tiny symmetric 3x3 eigen solver via Jacobi rotation.
# Returns (eigenvalues, eigenvectors) with eigenvalues sorted descending.
# eigenvectors are the columns of the returned 3x3 matrix (as list of rows).
# This is enough for PCA on a small covariance matrix.
# ---------------------------------------------------------------------------

def _jacobi_eigen_3x3(A):
    """
    A : 3x3 symmetric matrix, represented as list of 3 lists.
    Returns : (evals, evecs)
        evals : (l1, l2, l3)   sorted descending
        evecs : 3x3 list-of-rows, each column is a unit eigenvector
                matching the corresponding eigenvalue position.
    """
    # Make a mutable copy
    a = [row[:] for row in A]
    # Identity for accumulated rotations (eigenvectors as columns)
    v = [[1.0, 0.0, 0.0],
         [0.0, 1.0, 0.0],
         [0.0, 0.0, 1.0]]

    for _ in range(64):
        # Find largest off-diagonal magnitude
        p, q = 0, 1
        off_max = abs(a[0][1])
        if abs(a[0][2]) > off_max:
            p, q = 0, 2
            off_max = abs(a[0][2])
        if abs(a[1][2]) > off_max:
            p, q = 1, 2
            off_max = abs(a[1][2])

        if off_max < 1e-12:
            break  # converged

        app = a[p][p]
        aqq = a[q][q]
        apq = a[p][q]

        if abs(apq) < 1e-20:
            break

        # Compute Jacobi rotation angle
        theta = (aqq - app) / (2.0 * apq)
        if theta >= 0.0:
            t = 1.0 / (theta + math.sqrt(1.0 + theta * theta))
        else:
            t = 1.0 / (theta - math.sqrt(1.0 + theta * theta))
        c = 1.0 / math.sqrt(1.0 + t * t)
        s = t * c

        # Update a
        a[p][p] = app - t * apq
        a[q][q] = aqq + t * apq
        a[p][q] = 0.0
        a[q][p] = 0.0
        for i in range(3):
            if i != p and i != q:
                aip = a[i][p]
                aiq = a[i][q]
                a[i][p] = c * aip - s * aiq
                a[p][i] = a[i][p]
                a[i][q] = s * aip + c * aiq
                a[q][i] = a[i][q]

        # Update eigenvector matrix
        for i in range(3):
            vip = v[i][p]
            viq = v[i][q]
            v[i][p] = c * vip - s * viq
            v[i][q] = s * vip + c * viq

    evals = (a[0][0], a[1][1], a[2][2])
    # Sort descending by eigenvalue, reorder columns of v
    order = sorted(range(3), key=lambda i: -evals[i])
    sorted_evals = tuple(evals[i] for i in order)
    sorted_v = [[v[row][order[col]] for col in range(3)] for row in range(3)]
    return sorted_evals, sorted_v


def _pca_principal_axis(points):
    """
    Returns (axis_unit_vector, centroid) for a list of 3D points.
    The axis is the first principal component (largest variance).
    """
    c = _centroid(points)
    # Build covariance matrix
    sxx = syy = szz = sxy = sxz = syz = 0.0
    for p in points:
        dx = p[0] - c[0]
        dy = p[1] - c[1]
        dz = p[2] - c[2]
        sxx += dx * dx
        syy += dy * dy
        szz += dz * dz
        sxy += dx * dy
        sxz += dx * dz
        syz += dy * dz
    n = max(1, len(points))
    cov = [[sxx / n, sxy / n, sxz / n],
           [sxy / n, syy / n, syz / n],
           [sxz / n, syz / n, szz / n]]
    evals, evecs = _jacobi_eigen_3x3(cov)
    # First column of evecs is the principal axis
    axis = (evecs[0][0], evecs[1][0], evecs[2][0])
    return _vnorm(axis), c


def _project_onto_axis(point, axis_origin, axis_dir):
    """
    Returns t such that (axis_origin + t * axis_dir) is the foot of perpendicular.
    axis_dir must be unit length.
    """
    d = _vsub(point, axis_origin)
    return _vdot(d, axis_dir)


def _build_orthonormal_basis(axis):
    """
    Given a unit axis vector, return two unit vectors (u, v) that together
    with `axis` form a right-handed orthonormal basis.
    """
    # Choose a helper not parallel to axis
    if abs(axis[0]) < 0.9:
        helper = (1.0, 0.0, 0.0)
    else:
        helper = (0.0, 1.0, 0.0)
    u = _vnorm(_vcross(axis, helper))
    v = _vnorm(_vcross(axis, u))
    return u, v


# ---------------------------------------------------------------------------
# MayaBridge  -- selection & mesh utilities
# ---------------------------------------------------------------------------
class MayaBridge(object):

    @staticmethod
    def get_selected_meshes():
        """
        Returns mesh shapes from current selection, including all descendants.
        Excludes intermediate objects.
        """
        if not MAYA_AVAILABLE:
            return []
        sel = cmds.ls(selection=True, long=True) or []
        shapes = []
        seen = set()
        for node in sel:
            try:
                nt = cmds.nodeType(node)
            except Exception:
                continue
            if nt == "mesh":
                if node in seen:
                    continue
                try:
                    if cmds.getAttr(node + ".intermediateObject"):
                        continue
                except Exception:
                    pass
                shapes.append(node)
                seen.add(node)
            elif nt == "transform":
                ch = cmds.listRelatives(
                    node, allDescendents=True,
                    type="mesh", fullPath=True) or []
                for s in ch:
                    if s in seen:
                        continue
                    try:
                        if cmds.getAttr(s + ".intermediateObject"):
                            continue
                    except Exception:
                        pass
                    shapes.append(s)
                    seen.add(s)
        return shapes

    @staticmethod
    def get_short_name(long_name):
        parts = long_name.split("|")
        return parts[-1] if parts else long_name

    @staticmethod
    def get_transform(shape_name):
        """Returns the parent transform of a shape (long path)."""
        if not MAYA_AVAILABLE:
            return shape_name
        parents = cmds.listRelatives(shape_name, parent=True, fullPath=True) or []
        return parents[0] if parents else shape_name

    @staticmethod
    def get_vertex_positions_world(mesh_shape):
        """
        Returns a list of (x, y, z) tuples for each vertex in world space.
        """
        if not MAYA_AVAILABLE:
            return []
        sel = om.MSelectionList()
        sel.add(mesh_shape)
        dag = om.MDagPath()
        sel.getDagPath(0, dag)
        try:
            dag.extendToShape()
        except Exception:
            pass
        fn = om.MFnMesh(dag)
        pts = om.MPointArray()
        fn.getPoints(pts, om.MSpace.kWorld)
        out = []
        n = pts.length()
        for i in range(n):
            p = pts[i]
            out.append((p.x, p.y, p.z))
        return out

    @staticmethod
    def set_vertex_positions_world(mesh_shape, positions):
        """
        Overwrites the mesh vertex positions in world space.
        positions: list of (x, y, z) with len == mesh vertex count.
        """
        if not MAYA_AVAILABLE:
            return
        sel = om.MSelectionList()
        sel.add(mesh_shape)
        dag = om.MDagPath()
        sel.getDagPath(0, dag)
        try:
            dag.extendToShape()
        except Exception:
            pass
        fn = om.MFnMesh(dag)
        arr = om.MPointArray()
        arr.setLength(len(positions))
        for i, p in enumerate(positions):
            arr.set(om.MPoint(float(p[0]), float(p[1]), float(p[2]), 1.0), i)
        fn.setPoints(arr, om.MSpace.kWorld)

    @staticmethod
    def get_face_vertex_counts(mesh_shape):
        """Returns list where entry i = vertex count of polygon i."""
        if not MAYA_AVAILABLE:
            return []
        sel = om.MSelectionList()
        sel.add(mesh_shape)
        dag = om.MDagPath()
        sel.getDagPath(0, dag)
        try:
            dag.extendToShape()
        except Exception:
            pass
        fn = om.MFnMesh(dag)
        n_poly = fn.numPolygons()
        out = []
        verts = om.MIntArray()
        for i in range(n_poly):
            fn.getPolygonVertices(i, verts)
            out.append(verts.length())
        return out

    @staticmethod
    def get_polygon_vertices(mesh_shape):
        """Returns list of lists: [[v0,v1,v2,v3], [v0,v1,v2], ...]
        with vertex indices for each polygon face in order."""
        if not MAYA_AVAILABLE:
            return []
        sel = om.MSelectionList()
        sel.add(mesh_shape)
        dag = om.MDagPath()
        sel.getDagPath(0, dag)
        try:
            dag.extendToShape()
        except Exception:
            pass
        fn = om.MFnMesh(dag)
        n_poly = fn.numPolygons()
        verts = om.MIntArray()
        out = []
        for i in range(n_poly):
            fn.getPolygonVertices(i, verts)
            out.append([verts[k] for k in range(verts.length())])
        return out


# ---------------------------------------------------------------------------
# Cylinder Analyzer
# ---------------------------------------------------------------------------
# Given a mesh shape, determine:
#   - principal axis (or user-specified axis)
#   - ring structure (groups of vertices at similar axis position)
#   - per-ring center and mean/median radius
#   - number of sides (most common ring-vertex-count)
# This information is shared by both Cleanup and Change-Sides operations.
# ---------------------------------------------------------------------------

_AXIS_WORLD = {
    "x": (1.0, 0.0, 0.0),
    "y": (0.0, 1.0, 0.0),
    "z": (0.0, 0.0, 1.0),
}


def _compute_ring_radii_and_center(vert_ids, positions, axis_origin, axis_dir):
    """Helper: for a set of vertex indices assumed to lie in a ring around
    axis, return (center_point_on_axis, mean_radius, median_radius, radii_list)."""
    ts = []
    for i in vert_ids:
        p = positions[i]
        d = _vsub(p, axis_origin)
        ts.append(_vdot(d, axis_dir))
    t_mean = sum(ts) / len(ts)
    center = _vadd(axis_origin, _vmul(axis_dir, t_mean))
    radii = []
    for i in vert_ids:
        p = positions[i]
        d = _vsub(p, center)
        t_comp = _vdot(d, axis_dir)
        perp = _vsub(d, _vmul(axis_dir, t_comp))
        radii.append(_vlen(perp))
    mean_r = sum(radii) / len(radii) if radii else 0.0
    med_r = _median(radii)
    return center, mean_r, med_r, radii, t_mean


def analyze_cylinder(mesh_shape, axis_choice="auto"):
    """
    Analyze a mesh as a cylinder.

    axis_choice : "auto" | "x" | "y" | "z"   (local-space axis selection)

    Returns a dict:
        {
          "axis":       (ux, uy, uz) unit vector in world space,
          "origin":     (ox, oy, oz) a point on axis (the vertex centroid),
          "rings":      [ {verts, t, center, mean_r, median_r, radii} ... ],
                        sorted ascending by t,
          "sides":      int, detected side count (mode of ring sizes),
          "positions":  [(x,y,z) ...] per vertex, world space,
          "cap_vert_ids": set(int) -- vertices that don't fit any ring,
          "ring_tolerance": float used for clustering,
        }
    or None if the mesh can't be analyzed as a cylinder.
    """
    if not MAYA_AVAILABLE:
        return None

    positions = MayaBridge.get_vertex_positions_world(mesh_shape)
    if len(positions) < 6:
        return None

    # ---- Determine axis ----
    if axis_choice == "auto":
        axis, origin = _pca_principal_axis(positions)
    else:
        local_axis = _AXIS_WORLD.get(axis_choice.lower(), (0.0, 1.0, 0.0))
        # Transform the local-space axis into world space via the
        # transform node's world matrix.
        try:
            xform = MayaBridge.get_transform(mesh_shape)
            mtx = cmds.xform(xform, query=True, matrix=True, worldSpace=True)
            # matrix order in Maya: row-major 4x4, axis basis vectors at
            # [0:3]=X, [4:7]=Y, [8:11]=Z
            lax = local_axis
            wx = (mtx[0] * lax[0] + mtx[4] * lax[1] + mtx[8]  * lax[2])
            wy = (mtx[1] * lax[0] + mtx[5] * lax[1] + mtx[9]  * lax[2])
            wz = (mtx[2] * lax[0] + mtx[6] * lax[1] + mtx[10] * lax[2])
            axis = _vnorm((wx, wy, wz))
        except Exception:
            axis = _vnorm(local_axis)
        origin = _centroid(positions)

    if _vlen(axis) < 0.5:
        return None

    # ---- Project onto axis, find extent ----
    t_values = [_project_onto_axis(p, origin, axis) for p in positions]
    t_min = min(t_values)
    t_max = max(t_values)
    extent = t_max - t_min
    if extent < _EPS:
        return None

    # ---- Cluster verts into rings by axis position ----
    # Use an adaptive tolerance: start at 0.5% of extent, grow if we don't
    # produce enough multi-vertex rings (mesh might be very dense along axis).
    tol = max(extent * 0.005, 1e-6)

    # Sort vertex indices by t
    order = sorted(range(len(positions)), key=lambda i: t_values[i])
    rings = [[order[0]]]
    ref_t = t_values[order[0]]
    for idx in order[1:]:
        if abs(t_values[idx] - ref_t) < tol:
            rings[-1].append(idx)
        else:
            rings.append([idx])
        # Always update ref to the latest entry so drift works
        ref_t = t_values[idx]

    # Keep rings of size >= 3 (can't define a circle with fewer)
    side_rings = [r for r in rings if len(r) >= 3]
    if len(side_rings) < 2:
        return None

    # Detect side count = mode of ring sizes
    sizes = [len(r) for r in side_rings]
    # Mode
    size_counts = {}
    for s in sizes:
        size_counts[s] = size_counts.get(s, 0) + 1
    mode_sides = max(size_counts.items(), key=lambda kv: (kv[1], kv[0]))[0]

    # Keep only rings whose size matches mode (ignore odd-sized rings,
    # those are likely noise / caps with subdivided fans)
    valid_rings = [r for r in side_rings if len(r) == mode_sides]
    if len(valid_rings) < 2:
        return None

    # Compute ring details
    ring_details = []
    for r in valid_rings:
        center, mean_r, med_r, radii, t_mean = _compute_ring_radii_and_center(
            r, positions, origin, axis)
        ring_details.append({
            "verts":    r,
            "t":        t_mean,
            "center":   center,
            "mean_r":   mean_r,
            "median_r": med_r,
            "radii":    radii,
        })

    # Sort rings ascending by t
    ring_details.sort(key=lambda rd: rd["t"])

    # Collect cap verts (those not in any valid ring)
    ring_vert_set = set()
    for rd in ring_details:
        ring_vert_set.update(rd["verts"])
    cap_verts = set(range(len(positions))) - ring_vert_set

    return {
        "axis":           axis,
        "origin":         origin,
        "rings":          ring_details,
        "sides":          mode_sides,
        "positions":      positions,
        "cap_vert_ids":   cap_verts,
        "ring_tolerance": tol,
    }


def _axis_name_from_vector(axis, tol=0.05):
    """Return 'X', 'Y', 'Z', or '~' (arbitrary) depending on axis direction."""
    ax, ay, az = abs(axis[0]), abs(axis[1]), abs(axis[2])
    if ax > 1 - tol:
        return "X"
    if ay > 1 - tol:
        return "Y"
    if az > 1 - tol:
        return "Z"
    return u"~"   # non-aligned

# ---------------------------------------------------------------------------
# Cylinder Cleanup
# ---------------------------------------------------------------------------
# Non-destructive: only vertex positions are modified. Topology and UVs
# are preserved.
# Modes:
#   "full"   -> equalize angular spacing AND radii per ring  (perfectly regular)
#   "radius" -> equalize radii per ring, keep original angles
# Radius policy:
#   "mean"   -> use per-ring mean radius
#   "median" -> use per-ring median (robust to outlier verts)
# ---------------------------------------------------------------------------

def _compute_ring_angles(ring_verts, positions, center, u_vec, v_vec):
    """Return per-vertex angle (radians, -pi..pi) around the ring center
    using the (u, v) basis that is perpendicular to the cylinder axis."""
    out = []
    for i in ring_verts:
        p = positions[i]
        d = _vsub(p, center)
        du = _vdot(d, u_vec)
        dv = _vdot(d, v_vec)
        out.append(math.atan2(dv, du))
    return out


def cleanup_cylinder(analysis, mesh_shape, mode="full", radius_policy="mean"):
    """
    Apply cleanup to the mesh based on the pre-computed analysis.
    Returns (ring_count, side_count).
    """
    if analysis is None:
        return None

    axis = analysis["axis"]
    origin = analysis["origin"]
    u_vec, v_vec = _build_orthonormal_basis(axis)
    positions = list(analysis["positions"])  # copy
    new_positions = list(positions)

    for ring in analysis["rings"]:
        center = ring["center"]
        verts  = ring["verts"]
        N = len(verts)
        if N < 3:
            continue

        target_r = (ring["median_r"]
                    if radius_policy == "median"
                    else ring["mean_r"])

        # Per-vertex angle in the ring plane
        angles = _compute_ring_angles(verts, positions, center, u_vec, v_vec)

        if mode == "full":
            # Sort vertices by angle, then assign evenly-spaced angles in
            # sorted order. Use the smallest angle as base so the ring is
            # anchored to its original orientation (prevents rotation jumps).
            order = sorted(range(N), key=lambda k: angles[k])
            base_angle = angles[order[0]]
            for pos, k in enumerate(order):
                new_angle = base_angle + 2.0 * math.pi * pos / N
                new_p = _vadd(
                    center,
                    _vadd(_vmul(u_vec, target_r * math.cos(new_angle)),
                          _vmul(v_vec, target_r * math.sin(new_angle))))
                new_positions[verts[k]] = new_p
        else:
            # Radius-only: keep each vertex's original angle, force radius
            for k in range(N):
                a = angles[k]
                new_p = _vadd(
                    center,
                    _vadd(_vmul(u_vec, target_r * math.cos(a)),
                          _vmul(v_vec, target_r * math.sin(a))))
                new_positions[verts[k]] = new_p

    # Cap center vertices (vertices not in any detected ring) are snapped
    # to the axis line at their original t-projection so the n-gon-fan cap
    # centers sit nicely on the axis.
    for i in analysis["cap_vert_ids"]:
        p = positions[i]
        d = _vsub(p, origin)
        t = _vdot(d, axis)
        new_positions[i] = _vadd(origin, _vmul(axis, t))

    MayaBridge.set_vertex_positions_world(mesh_shape, new_positions)
    return (len(analysis["rings"]), analysis["sides"])

# ---------------------------------------------------------------------------
# Cylinder -- Change Sides (N <-> M)
# ---------------------------------------------------------------------------
# Creates a NEW mesh that preserves the per-ring axis position and radius
# of the source, but uses `target_sides` vertices per ring.
# Optionally deletes the source ("replace") or keeps both ("duplicate").
# UV layout is recreated via Maya's cylindrical projection.
# ---------------------------------------------------------------------------

def _axis_to_local_option(axis_world):
    """Return best-guess world axis hint for cmds.polyProjection:
    "X", "Y", or "Z" depending on the dominant component."""
    ax, ay, az = abs(axis_world[0]), abs(axis_world[1]), abs(axis_world[2])
    if ax >= ay and ax >= az:
        return "X"
    if ay >= ax and ay >= az:
        return "Y"
    return "Z"


def resides_cylinder(analysis, mesh_shape, target_sides,
                      create_caps=True, replace=False,
                      preserve_uv=True):
    """
    Rebuild the selected cylinder with `target_sides` vertices per ring.

    analysis      : dict returned by analyze_cylinder()
    mesh_shape    : source mesh shape (long path)
    target_sides  : int, 3..128
    create_caps   : bool, add n-gon end caps
    replace       : bool, delete original after build and take its name/parent
    preserve_uv   : bool, apply cylindrical UV projection
    Returns new transform long path.
    """
    if analysis is None:
        raise RuntimeError("analysis is None")
    if target_sides < 3 or target_sides > 128:
        raise ValueError("target_sides must be in 3..128")

    axis = analysis["axis"]
    rings = analysis["rings"]
    if len(rings) < 2:
        raise RuntimeError("Need at least 2 rings to rebuild cylinder")

    M = int(target_sides)
    u_vec, v_vec = _build_orthonormal_basis(axis)

    # Determine a consistent base angle so the generated mesh's "seam"
    # lines up with the source's seam. Use the original first-ring's
    # first-by-vertex-index vertex angle as reference.
    first_ring = rings[0]
    first_verts = first_ring["verts"]
    base_vert_local_index = min(
        range(len(first_verts)), key=lambda i: first_verts[i])
    base_angle = _compute_ring_angles(
        [first_verts[base_vert_local_index]], analysis["positions"],
        first_ring["center"], u_vec, v_vec)[0]

    # ---- Build new vertex list (world space) ----
    new_verts = []
    for ring in rings:
        center = ring["center"]
        r = ring["mean_r"]
        for i in range(M):
            a = base_angle + 2.0 * math.pi * i / M
            p = _vadd(center,
                      _vadd(_vmul(u_vec, r * math.cos(a)),
                            _vmul(v_vec, r * math.sin(a))))
            new_verts.append(p)

    # ---- Build face connectivity ----
    n_rings = len(rings)
    faces = []
    # Side quads: winding v[ri,si] -> v[ri,si+1] -> v[ri+1,si+1] -> v[ri+1,si]
    for ri in range(n_rings - 1):
        base_lo = ri * M
        base_hi = (ri + 1) * M
        for si in range(M):
            a = base_lo + si
            b = base_lo + (si + 1) % M
            c = base_hi + (si + 1) % M
            d = base_hi + si
            faces.append([a, b, c, d])

    # Caps: bottom (first ring) with reversed winding so normal points -axis;
    # top (last ring) with natural winding so normal points +axis.
    if create_caps:
        bottom = list(range(M))
        bottom.reverse()
        top = [(n_rings - 1) * M + i for i in range(M)]
        faces.append(bottom)
        faces.append(top)

    # ---- Create the mesh via OpenMaya ----
    points = om.MPointArray()
    points.setLength(len(new_verts))
    for i, p in enumerate(new_verts):
        points.set(om.MPoint(float(p[0]), float(p[1]), float(p[2]), 1.0), i)

    face_counts = om.MIntArray()
    face_connects = om.MIntArray()
    for f in faces:
        face_counts.append(len(f))
        for v in f:
            face_connects.append(int(v))

    # Make a new transform node as parent for the mesh
    src_transform = MayaBridge.get_transform(mesh_shape)
    src_short = MayaBridge.get_short_name(src_transform)
    new_name_hint = src_short + "_remeshed"

    new_xform = cmds.createNode("transform", name=new_name_hint)
    # Get MObject of that transform
    sel = om.MSelectionList()
    sel.add(new_xform)
    parent_mo = om.MObject()
    sel.getDependNode(0, parent_mo)

    fn_mesh = om.MFnMesh()
    try:
        fn_mesh.create(
            len(new_verts), len(faces),
            points, face_counts, face_connects,
            parent_mo,
        )
    except Exception as e:
        # Clean up empty transform if creation failed
        try:
            cmds.delete(new_xform)
        except Exception:
            pass
        raise RuntimeError("Failed to create mesh: " + str(e))

    # The new mesh shape was parented under new_xform. Find it.
    new_shapes = cmds.listRelatives(new_xform, shapes=True, fullPath=True) or []
    if not new_shapes:
        raise RuntimeError("Created mesh has no shape node")
    new_shape = new_shapes[0]

    # Assign default lambert shader
    try:
        cmds.sets(new_shape, edit=True, forceElement="initialShadingGroup")
    except Exception:
        pass

    # ---- UV: cylindrical projection aligned to axis ----
    if preserve_uv:
        try:
            axis_hint = _axis_to_local_option(axis)
            # polyProjection -cm True -type Cylindrical
            # -ibd True = insert before deformers (not needed for new mesh, but safe)
            cmds.polyProjection(
                new_shape + ".f[*]",
                type="Cylindrical",
                md=axis_hint,       # map direction (X, Y, or Z)
                ch=False)
        except Exception:
            pass

    # ---- Parent / naming ----
    # Ensure new transform is at identity (verts were built in world space)
    try:
        cmds.xform(new_xform, worldSpace=True,
                   translation=(0.0, 0.0, 0.0),
                   rotation=(0.0, 0.0, 0.0),
                   scale=(1.0, 1.0, 1.0))
    except Exception:
        pass

    # Preserve hierarchy: place new_xform under the same parent as src_transform
    src_parents = cmds.listRelatives(src_transform, parent=True, fullPath=True)
    if src_parents:
        try:
            cmds.parent(new_xform, src_parents[0])
        except Exception:
            pass

    final_xform = new_xform
    if replace:
        try:
            # Collect original long name before deleting
            original_name = MayaBridge.get_short_name(src_transform)
            cmds.delete(src_transform)
            final_xform = cmds.rename(new_xform, original_name)
        except Exception:
            # If delete/rename fails, leave the duplicated mesh in place
            final_xform = new_xform

    # Return the long path of the final transform
    try:
        final_long = cmds.ls(final_xform, long=True)
        if final_long:
            return final_long[0]
    except Exception:
        pass
    return final_xform

# ---------------------------------------------------------------------------
# Shared UI helpers & stylesheets
# ---------------------------------------------------------------------------
def _mkbtn(text, h, bg, hv, fs=11, parent=None):
    b = QtWidgets.QPushButton(text, parent)
    b.setFixedHeight(h)
    b.setStyleSheet(
        "QPushButton{{background-color:{bg};color:white;border:none;"
        "border-radius:4px;font-size:{fs}px;font-weight:bold;padding:0 10px}}"
        "QPushButton:hover{{background-color:{hv}}}"
        "QPushButton:disabled{{background-color:#444;color:#666}}"
        .format(bg=bg, hv=hv, fs=fs))
    return b


_DIALOG_SS = (
    "QDialog{background-color:#333;color:#EEE}"
    "QGroupBox{border:1px solid #555;border-radius:6px;"
    "background-color:#2E2E2E;color:#EEE;margin-top:8px;padding-top:8px}"
    "QGroupBox::title{subcontrol-origin:margin;left:8px}"
    "QLabel{color:#EEE}"
    "QCheckBox{color:#EEE}"
    "QDoubleSpinBox,QSpinBox,QLineEdit{"
    "background-color:#2B2B2B;color:#EEE;border:1px solid #555;"
    "border-radius:3px;padding:2px}"
    "QListWidget{background-color:#2B2B2B;color:#EEE;"
    "border:1px solid #555;border-radius:3px}"
    "QListWidget::item:selected{background-color:#1565C0}"
)


# Small grey label (used for form field labels)
_LBL_SS = "color:#AAA;font-size:10px"

# Read-only line edit ("pill")
_FIELD_SS = ("QLineEdit{background-color:#2B2B2B;color:#EEE;"
             "border:1px solid #555;border-radius:3px;"
             "padding:2px 4px;font-size:10px}")

# Spin box (int / double)
_SPIN_SS = ("QDoubleSpinBox,QSpinBox{background-color:#2B2B2B;color:#EEE;"
            "border:1px solid #555;border-radius:3px;"
            "padding:1px;font-size:10px}")

# [Set] selection-pickup button (grey)
_SET_BTN_SS = ("QPushButton{background-color:#455A64;color:#EEE;"
               "border:1px solid #607D8B;border-radius:3px;"
               "font-size:10px;padding:2px 8px}"
               "QPushButton:hover{background-color:#546E7A}")

# Radio buttons (small neutral)
_RADIO_SS = "QRadioButton{color:#CCC;font-size:10px}"

# Small light-grey checkbox
_CB_SS = ("QCheckBox{color:#CCC;font-size:10px}"
          "QCheckBox::indicator{width:12px;height:12px}")


# ---------------------------------------------------------------------------
# Cylinder Cleanup UI  (Pattern C -- form)
# ---------------------------------------------------------------------------
# Attaches runtime state and widgets to the parent tool window as `_cc_*`.
# Called from the main window build step.
# ---------------------------------------------------------------------------


def _cc_build_group(tool_window, parent_layout):
    """Build the Cleanup form group and append to parent_layout."""
    tool_window._cc_target_shape = None   # long path
    tool_window._cc_last_analysis = None  # cached analysis dict

    grp = QtWidgets.QGroupBox()
    grp.setStyleSheet(
        "QGroupBox{border:1px solid #2196F3;border-radius:6px;"
        "background-color:#2E2E2E;margin-top:6px}"
        "QGroupBox::title{subcontrol-origin:margin;left:10px;"
        "color:#EEE;font-size:11px;font-weight:bold}")
    lo = QtWidgets.QVBoxLayout(grp)
    lo.setContentsMargins(8, 12, 8, 8)
    lo.setSpacing(6)

    # Header label
    tool_window._cc_grp_lbl = QtWidgets.QLabel(
        u"\u25A0 " + tr("cc_grp_title"))
    tool_window._cc_grp_lbl.setStyleSheet(
        "color:#2196F3;font-size:11px;font-weight:bold")
    lo.addWidget(tool_window._cc_grp_lbl)

    # Target row
    row = QtWidgets.QHBoxLayout()
    tool_window._cc_lbl_target = QtWidgets.QLabel(tr("cc_lbl_target"))
    tool_window._cc_lbl_target.setStyleSheet(_LBL_SS)
    tool_window._cc_lbl_target.setFixedWidth(110)
    row.addWidget(tool_window._cc_lbl_target)
    tool_window._cc_txt_target = QtWidgets.QLineEdit()
    tool_window._cc_txt_target.setReadOnly(True)
    tool_window._cc_txt_target.setStyleSheet(_FIELD_SS)
    row.addWidget(tool_window._cc_txt_target)
    tool_window._cc_btn_set = QtWidgets.QPushButton(tr("btn_set"))
    tool_window._cc_btn_set.setStyleSheet(_SET_BTN_SS)
    tool_window._cc_btn_set.setFixedWidth(50)
    tool_window._cc_btn_set.clicked.connect(
        lambda: _cc_set_target(tool_window))
    row.addWidget(tool_window._cc_btn_set)
    lo.addLayout(row)

    # Info label (detected axis / rings / sides)
    tool_window._cc_info_lbl = QtWidgets.QLabel(u"")
    tool_window._cc_info_lbl.setStyleSheet(
        "color:#888;font-size:10px;padding:2px 0 0 110px")
    lo.addWidget(tool_window._cc_info_lbl)

    # Separator
    sep = QtWidgets.QFrame()
    sep.setFrameShape(QtWidgets.QFrame.HLine)
    sep.setStyleSheet("color:#555")
    lo.addWidget(sep)

    # Axis row
    ax_row = QtWidgets.QHBoxLayout()
    tool_window._cc_lbl_axis = QtWidgets.QLabel(tr("cc_lbl_axis"))
    tool_window._cc_lbl_axis.setStyleSheet(_LBL_SS)
    tool_window._cc_lbl_axis.setFixedWidth(110)
    ax_row.addWidget(tool_window._cc_lbl_axis)
    tool_window._cc_rb_auto = QtWidgets.QRadioButton(tr("cc_ax_auto"))
    tool_window._cc_rb_x    = QtWidgets.QRadioButton("X")
    tool_window._cc_rb_y    = QtWidgets.QRadioButton("Y")
    tool_window._cc_rb_z    = QtWidgets.QRadioButton("Z")
    tool_window._cc_rb_auto.setChecked(True)
    ax_grp = QtWidgets.QButtonGroup(tool_window)
    for rb in (tool_window._cc_rb_auto, tool_window._cc_rb_x,
               tool_window._cc_rb_y, tool_window._cc_rb_z):
        rb.setStyleSheet(_RADIO_SS)
        ax_grp.addButton(rb)
        ax_row.addWidget(rb)
    ax_row.addStretch()
    tool_window._cc_ax_group = ax_grp
    for rb in (tool_window._cc_rb_auto, tool_window._cc_rb_x,
               tool_window._cc_rb_y, tool_window._cc_rb_z):
        rb.toggled.connect(lambda _c, tw=tool_window: _cc_refresh_preview(tw))
    lo.addLayout(ax_row)

    # Mode row
    mo_row = QtWidgets.QHBoxLayout()
    tool_window._cc_lbl_mode = QtWidgets.QLabel(tr("cc_lbl_mode"))
    tool_window._cc_lbl_mode.setStyleSheet(_LBL_SS)
    tool_window._cc_lbl_mode.setFixedWidth(110)
    mo_row.addWidget(tool_window._cc_lbl_mode)
    tool_window._cc_rb_mode_full = QtWidgets.QRadioButton(tr("cc_mode_full"))
    tool_window._cc_rb_mode_rad  = QtWidgets.QRadioButton(tr("cc_mode_radius"))
    tool_window._cc_rb_mode_full.setChecked(True)
    mo_grp = QtWidgets.QButtonGroup(tool_window)
    for rb in (tool_window._cc_rb_mode_full, tool_window._cc_rb_mode_rad):
        rb.setStyleSheet(_RADIO_SS)
        mo_grp.addButton(rb)
        mo_row.addWidget(rb)
    mo_row.addStretch()
    tool_window._cc_mode_group = mo_grp
    lo.addLayout(mo_row)

    # Radius policy row
    rp_row = QtWidgets.QHBoxLayout()
    tool_window._cc_lbl_rpol = QtWidgets.QLabel(tr("cc_lbl_radius_avg"))
    tool_window._cc_lbl_rpol.setStyleSheet(_LBL_SS)
    tool_window._cc_lbl_rpol.setFixedWidth(110)
    rp_row.addWidget(tool_window._cc_lbl_rpol)
    tool_window._cc_rb_rpol_mean = QtWidgets.QRadioButton(tr("cc_radius_mean"))
    tool_window._cc_rb_rpol_med  = QtWidgets.QRadioButton(tr("cc_radius_median"))
    tool_window._cc_rb_rpol_mean.setChecked(True)
    rpol_grp = QtWidgets.QButtonGroup(tool_window)
    for rb in (tool_window._cc_rb_rpol_mean, tool_window._cc_rb_rpol_med):
        rb.setStyleSheet(_RADIO_SS)
        rpol_grp.addButton(rb)
        rp_row.addWidget(rb)
    rp_row.addStretch()
    tool_window._cc_rpol_group = rpol_grp
    lo.addLayout(rp_row)

    # Apply button
    btn_row = QtWidgets.QHBoxLayout()
    btn_row.addStretch()
    tool_window._cc_btn_apply = _mkbtn(tr("cc_btn_apply"), 28,
                                       "#2196F3", "#1976D2")
    tool_window._cc_btn_apply.setFixedWidth(140)
    tool_window._cc_btn_apply.clicked.connect(
        lambda: _cc_on_apply(tool_window))
    btn_row.addWidget(tool_window._cc_btn_apply)
    btn_row.addStretch()
    lo.addLayout(btn_row)

    parent_layout.addWidget(grp)
    return grp


# ---------------------------------------------------------------------------
# UI handlers
# ---------------------------------------------------------------------------

def _cc_set_status(tool_window, text):
    if hasattr(tool_window, "_status_bar"):
        tool_window._status_bar.setText(text)


def _cc_current_axis_choice(tool_window):
    if tool_window._cc_rb_x.isChecked(): return "x"
    if tool_window._cc_rb_y.isChecked(): return "y"
    if tool_window._cc_rb_z.isChecked(): return "z"
    return "auto"


def _cc_current_mode(tool_window):
    if tool_window._cc_rb_mode_rad.isChecked():
        return "radius"
    return "full"


def _cc_current_radius_policy(tool_window):
    if tool_window._cc_rb_rpol_med.isChecked():
        return "median"
    return "mean"


def _cc_set_target(tool_window):
    if not MAYA_AVAILABLE:
        return
    shapes = MayaBridge.get_selected_meshes()
    if not shapes:
        tool_window._cc_target_shape = None
        tool_window._cc_txt_target.setText(u"---")
        tool_window._cc_info_lbl.setText(u"")
        _cc_set_status(tool_window, tr("status_no_mesh"))
        return
    shape = shapes[0]
    tool_window._cc_target_shape = shape
    tool_window._cc_txt_target.setText(MayaBridge.get_short_name(
        MayaBridge.get_transform(shape)))
    _cc_set_status(tool_window, tr("status_target_set",
                                   name=MayaBridge.get_short_name(shape)))
    _cc_refresh_preview(tool_window)


def _cc_refresh_preview(tool_window):
    """Re-run analysis with current axis choice and update info label."""
    if not tool_window._cc_target_shape:
        tool_window._cc_info_lbl.setText(u"")
        tool_window._cc_last_analysis = None
        return
    axis_choice = _cc_current_axis_choice(tool_window)
    try:
        analysis = analyze_cylinder(tool_window._cc_target_shape,
                                    axis_choice=axis_choice)
    except Exception:
        analysis = None
    tool_window._cc_last_analysis = analysis
    if analysis is None:
        tool_window._cc_info_lbl.setText(tr("status_not_cyl"))
        return
    ax_name = _axis_name_from_vector(analysis["axis"])
    tool_window._cc_info_lbl.setText(tr(
        "cc_info_detected",
        axis=ax_name,
        rings=len(analysis["rings"]),
        sides=analysis["sides"]))


def _cc_on_apply(tool_window):
    if not MAYA_AVAILABLE:
        return
    if not tool_window._cc_target_shape:
        _cc_set_status(tool_window, tr("status_target_not_set"))
        return

    axis_choice = _cc_current_axis_choice(tool_window)
    try:
        analysis = analyze_cylinder(tool_window._cc_target_shape,
                                    axis_choice=axis_choice)
    except Exception as e:
        _cc_set_status(tool_window, tr("status_error", msg=str(e)))
        return

    if analysis is None:
        _cc_set_status(tool_window, tr("status_not_cyl"))
        return

    mode = _cc_current_mode(tool_window)
    rpol = _cc_current_radius_policy(tool_window)

    cmds.undoInfo(openChunk=True, chunkName="DW_CylinderCleanup")
    try:
        rings_cnt, side_cnt = cleanup_cylinder(
            analysis, tool_window._cc_target_shape,
            mode=mode, radius_policy=rpol) or (0, 0)
        ax_name = _axis_name_from_vector(analysis["axis"])
        _cc_set_status(tool_window, tr(
            "status_cleanup_done",
            axis=ax_name, rings=rings_cnt, sides=side_cnt))
        _cc_refresh_preview(tool_window)
    except Exception as e:
        import traceback
        traceback.print_exc()
        _cc_set_status(tool_window, tr("status_error", msg=str(e)))
    finally:
        cmds.undoInfo(closeChunk=True)


def _cc_refresh_labels(tool_window):
    if not hasattr(tool_window, "_cc_grp_lbl"):
        return
    tool_window._cc_grp_lbl.setText(u"\u25A0 " + tr("cc_grp_title"))
    tool_window._cc_lbl_target.setText(tr("cc_lbl_target"))
    tool_window._cc_btn_set.setText(tr("btn_set"))
    tool_window._cc_lbl_axis.setText(tr("cc_lbl_axis"))
    tool_window._cc_rb_auto.setText(tr("cc_ax_auto"))
    tool_window._cc_lbl_mode.setText(tr("cc_lbl_mode"))
    tool_window._cc_rb_mode_full.setText(tr("cc_mode_full"))
    tool_window._cc_rb_mode_rad.setText(tr("cc_mode_radius"))
    tool_window._cc_lbl_rpol.setText(tr("cc_lbl_radius_avg"))
    tool_window._cc_rb_rpol_mean.setText(tr("cc_radius_mean"))
    tool_window._cc_rb_rpol_med.setText(tr("cc_radius_median"))
    tool_window._cc_btn_apply.setText(tr("cc_btn_apply"))
    _cc_refresh_preview(tool_window)

# ---------------------------------------------------------------------------
# Cylinder Change-Sides UI  (Pattern C -- form)
# ---------------------------------------------------------------------------

def _rs_build_group(tool_window, parent_layout):
    """Build the Change-Sides form group and append to parent_layout."""
    tool_window._rs_target_shape = None

    grp = QtWidgets.QGroupBox()
    grp.setStyleSheet(
        "QGroupBox{border:1px solid #4CAF50;border-radius:6px;"
        "background-color:#2E2E2E;margin-top:6px}"
        "QGroupBox::title{subcontrol-origin:margin;left:10px;"
        "color:#EEE;font-size:11px;font-weight:bold}")
    lo = QtWidgets.QVBoxLayout(grp)
    lo.setContentsMargins(8, 12, 8, 8)
    lo.setSpacing(6)

    tool_window._rs_grp_lbl = QtWidgets.QLabel(
        u"\u25A0 " + tr("rs_grp_title"))
    tool_window._rs_grp_lbl.setStyleSheet(
        "color:#4CAF50;font-size:11px;font-weight:bold")
    lo.addWidget(tool_window._rs_grp_lbl)

    # Target row
    row = QtWidgets.QHBoxLayout()
    tool_window._rs_lbl_target = QtWidgets.QLabel(tr("rs_lbl_target"))
    tool_window._rs_lbl_target.setStyleSheet(_LBL_SS)
    tool_window._rs_lbl_target.setFixedWidth(110)
    row.addWidget(tool_window._rs_lbl_target)
    tool_window._rs_txt_target = QtWidgets.QLineEdit()
    tool_window._rs_txt_target.setReadOnly(True)
    tool_window._rs_txt_target.setStyleSheet(_FIELD_SS)
    row.addWidget(tool_window._rs_txt_target)
    tool_window._rs_btn_set = QtWidgets.QPushButton(tr("btn_set"))
    tool_window._rs_btn_set.setStyleSheet(_SET_BTN_SS)
    tool_window._rs_btn_set.setFixedWidth(50)
    tool_window._rs_btn_set.clicked.connect(
        lambda: _rs_set_target(tool_window))
    row.addWidget(tool_window._rs_btn_set)
    lo.addLayout(row)

    # Current sides display
    cur_row = QtWidgets.QHBoxLayout()
    tool_window._rs_lbl_current = QtWidgets.QLabel(tr("rs_lbl_current"))
    tool_window._rs_lbl_current.setStyleSheet(_LBL_SS)
    tool_window._rs_lbl_current.setFixedWidth(110)
    cur_row.addWidget(tool_window._rs_lbl_current)
    tool_window._rs_txt_current = QtWidgets.QLineEdit(u"---")
    tool_window._rs_txt_current.setReadOnly(True)
    tool_window._rs_txt_current.setStyleSheet(_FIELD_SS)
    tool_window._rs_txt_current.setFixedWidth(75)
    cur_row.addWidget(tool_window._rs_txt_current)
    cur_row.addStretch()
    lo.addLayout(cur_row)

    # Separator
    sep = QtWidgets.QFrame()
    sep.setFrameShape(QtWidgets.QFrame.HLine)
    sep.setStyleSheet("color:#555")
    lo.addWidget(sep)

    # Target sides spin
    tgt_row = QtWidgets.QHBoxLayout()
    tool_window._rs_lbl_target_sides = QtWidgets.QLabel(tr("rs_lbl_target_sides"))
    tool_window._rs_lbl_target_sides.setStyleSheet(_LBL_SS)
    tool_window._rs_lbl_target_sides.setFixedWidth(110)
    tgt_row.addWidget(tool_window._rs_lbl_target_sides)
    tool_window._rs_spin_sides = QtWidgets.QSpinBox()
    tool_window._rs_spin_sides.setRange(3, 128)
    tool_window._rs_spin_sides.setValue(8)
    tool_window._rs_spin_sides.setFixedWidth(75)
    tool_window._rs_spin_sides.setStyleSheet(_SPIN_SS)
    tgt_row.addWidget(tool_window._rs_spin_sides)
    tgt_row.addStretch()
    lo.addLayout(tgt_row)

    # Options checkboxes
    tool_window._rs_cb_caps = QtWidgets.QCheckBox(tr("rs_chk_keep_caps"))
    tool_window._rs_cb_caps.setStyleSheet(_CB_SS)
    tool_window._rs_cb_caps.setChecked(True)
    lo.addWidget(tool_window._rs_cb_caps)

    tool_window._rs_cb_uv = QtWidgets.QCheckBox(tr("rs_chk_keep_uv"))
    tool_window._rs_cb_uv.setStyleSheet(_CB_SS)
    tool_window._rs_cb_uv.setChecked(True)
    lo.addWidget(tool_window._rs_cb_uv)

    tool_window._rs_cb_replace = QtWidgets.QCheckBox(tr("rs_chk_replace"))
    tool_window._rs_cb_replace.setStyleSheet(_CB_SS)
    tool_window._rs_cb_replace.setChecked(False)
    lo.addWidget(tool_window._rs_cb_replace)

    # Apply button
    btn_row = QtWidgets.QHBoxLayout()
    btn_row.addStretch()
    tool_window._rs_btn_apply = _mkbtn(tr("rs_btn_apply"), 28,
                                       "#4CAF50", "#388E3C")
    tool_window._rs_btn_apply.setFixedWidth(140)
    tool_window._rs_btn_apply.clicked.connect(
        lambda: _rs_on_apply(tool_window))
    btn_row.addWidget(tool_window._rs_btn_apply)
    btn_row.addStretch()
    lo.addLayout(btn_row)

    parent_layout.addWidget(grp)
    return grp


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _rs_set_status(tool_window, text):
    if hasattr(tool_window, "_status_bar"):
        tool_window._status_bar.setText(text)


def _rs_set_target(tool_window):
    if not MAYA_AVAILABLE:
        return
    shapes = MayaBridge.get_selected_meshes()
    if not shapes:
        tool_window._rs_target_shape = None
        tool_window._rs_txt_target.setText(u"---")
        tool_window._rs_txt_current.setText(u"---")
        _rs_set_status(tool_window, tr("status_no_mesh"))
        return
    shape = shapes[0]
    tool_window._rs_target_shape = shape
    tool_window._rs_txt_target.setText(MayaBridge.get_short_name(
        MayaBridge.get_transform(shape)))
    # Detect current sides
    try:
        analysis = analyze_cylinder(shape, axis_choice="auto")
    except Exception:
        analysis = None
    if analysis is None:
        tool_window._rs_txt_current.setText(u"---")
        _rs_set_status(tool_window, tr("status_not_cyl"))
        return
    tool_window._rs_txt_current.setText(u"{0}".format(analysis["sides"]))
    _rs_set_status(tool_window, tr("status_target_set",
                                   name=MayaBridge.get_short_name(shape)))


def _rs_on_apply(tool_window):
    if not MAYA_AVAILABLE:
        return
    if not tool_window._rs_target_shape:
        _rs_set_status(tool_window, tr("status_target_not_set"))
        return

    target_sides = int(tool_window._rs_spin_sides.value())
    create_caps = bool(tool_window._rs_cb_caps.isChecked())
    preserve_uv = bool(tool_window._rs_cb_uv.isChecked())
    replace     = bool(tool_window._rs_cb_replace.isChecked())

    # Always use auto axis for resides (we can expose the radio later)
    try:
        analysis = analyze_cylinder(tool_window._rs_target_shape,
                                    axis_choice="auto")
    except Exception as e:
        _rs_set_status(tool_window, tr("status_error", msg=str(e)))
        return

    if analysis is None:
        _rs_set_status(tool_window, tr("status_not_cyl"))
        return

    old_sides = analysis["sides"]
    rings_cnt = len(analysis["rings"])

    cmds.undoInfo(openChunk=True, chunkName="DW_CylinderResides")
    try:
        new_xform = resides_cylinder(
            analysis, tool_window._rs_target_shape,
            target_sides,
            create_caps=create_caps,
            replace=replace,
            preserve_uv=preserve_uv,
        )
        # If we replaced, the old shape is gone; pick up the new shape
        if replace and new_xform:
            new_shapes = cmds.listRelatives(
                new_xform, shapes=True, fullPath=True) or []
            if new_shapes:
                tool_window._rs_target_shape = new_shapes[0]
                tool_window._rs_txt_target.setText(
                    MayaBridge.get_short_name(new_xform))
                tool_window._rs_txt_current.setText(u"{0}".format(target_sides))
        _rs_set_status(tool_window, tr(
            "status_resides_done",
            old=old_sides, new=target_sides, rings=rings_cnt))
    except Exception as e:
        import traceback
        traceback.print_exc()
        _rs_set_status(tool_window, tr("status_error", msg=str(e)))
    finally:
        cmds.undoInfo(closeChunk=True)


def _rs_refresh_labels(tool_window):
    if not hasattr(tool_window, "_rs_grp_lbl"):
        return
    tool_window._rs_grp_lbl.setText(u"\u25A0 " + tr("rs_grp_title"))
    tool_window._rs_lbl_target.setText(tr("rs_lbl_target"))
    tool_window._rs_btn_set.setText(tr("btn_set"))
    tool_window._rs_lbl_current.setText(tr("rs_lbl_current"))
    tool_window._rs_lbl_target_sides.setText(tr("rs_lbl_target_sides"))
    tool_window._rs_cb_caps.setText(tr("rs_chk_keep_caps"))
    tool_window._rs_cb_uv.setText(tr("rs_chk_keep_uv"))
    tool_window._rs_cb_replace.setText(tr("rs_chk_replace"))
    tool_window._rs_btn_apply.setText(tr("rs_btn_apply"))

# ---------------------------------------------------------------------------
# RemesherToolWindow  (Main UI)
# ---------------------------------------------------------------------------
_MAIN_SS = (
    "QDialog{background-color:#333}"
    "QScrollArea{border:none;background-color:transparent}"
    "QScrollBar:vertical{background:#2B2B2B;width:10px}"
    "QScrollBar::handle:vertical{background:#555;border-radius:4px}"
    "QGroupBox{border-radius:6px;background-color:#2E2E2E;margin-top:6px}"
    "QGroupBox::title{subcontrol-origin:margin;left:10px;"
    "color:#EEE;font-size:11px;font-weight:bold}"
    "QLabel{color:#EEE}"
)


class RemesherToolWindow(QtWidgets.QDialog):

    def __init__(self, parent=None):
        if parent is None and MAYA_AVAILABLE:
            try:
                ptr = omui.MQtUtil.mainWindow()
                if PY2:
                    parent = wrapInstance(long(ptr), QtWidgets.QWidget)  # noqa: F821
                else:
                    parent = wrapInstance(int(ptr), QtWidgets.QWidget)
            except Exception:
                pass

        super(RemesherToolWindow, self).__init__(parent)
        self.setObjectName("DW_Remesher_Main")
        self.setWindowTitle(tr("window_title"))
        self.setMinimumWidth(420)
        self.setMinimumHeight(440)
        self.resize(440, 520)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.setStyleSheet(_MAIN_SS)

        self._build()

        if _saved_geometry:
            x, y, w, h = _saved_geometry
            self.setGeometry(x, y, w, h)
        else:
            self.adjustSize()

    # ------------------------------------------------------------------
    def _build(self):
        main_lo = QtWidgets.QVBoxLayout(self)
        main_lo.setContentsMargins(8, 8, 8, 8)
        main_lo.setSpacing(4)

        # ---- Header bar ----
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(4)

        self._title_lbl = QtWidgets.QLabel(
            u"<b>{0}</b> <span style='color:#888;font-size:10px'>v{1}</span>".format(
                tr("window_title"), VERSION))
        self._title_lbl.setStyleSheet("color:#EEE;font-size:14px;padding:4px")
        header.addWidget(self._title_lbl)
        header.addStretch()

        reload_btn = QtWidgets.QPushButton(u"\u21BB")
        reload_btn.setFixedSize(28, 24)
        reload_btn.setToolTip(tr("btn_reload"))
        reload_btn.setStyleSheet(
            "QPushButton{background-color:#555;color:#EEE;"
            "border:1px solid #777;border-radius:3px;font-size:14px}"
            "QPushButton:hover{background-color:#4CAF50}")
        reload_btn.clicked.connect(self._on_reload)
        header.addWidget(reload_btn)

        # Update button
        self._update_btn = QtWidgets.QPushButton(u"\u2B07")
        self._update_btn.setFixedSize(28, 24)
        self._update_btn.setToolTip(tr("btn_update"))
        self._update_btn.clicked.connect(self._on_check_update)
        header.addWidget(self._update_btn)
        self._set_update_btn_state("unknown")

        # Help button
        help_btn = QtWidgets.QPushButton("?")
        help_btn.setFixedSize(24, 24)
        help_btn.setStyleSheet(
            "QPushButton{background-color:#555;color:#EEE;"
            "border:1px solid #777;border-radius:3px;font-size:12px;font-weight:bold}"
            "QPushButton:hover{background-color:#2196F3}")
        help_btn.clicked.connect(self._open_help)
        header.addWidget(help_btn)

        # Language toggle
        self._lang_btn = QtWidgets.QPushButton(tr("btn_lang"))
        self._lang_btn.setFixedSize(36, 24)
        self._lang_btn.setStyleSheet(
            "QPushButton{background-color:#555;color:#EEE;"
            "border:1px solid #777;border-radius:3px;font-size:10px;font-weight:bold}"
            "QPushButton:hover{background-color:#607D8B}")
        self._lang_btn.clicked.connect(self._toggle_lang)
        header.addWidget(self._lang_btn)

        main_lo.addLayout(header)

        # ---- Tab widget (single tab: Cylinder) ----
        self._tabs = QtWidgets.QTabWidget()
        self._tabs.setStyleSheet(
            "QTabWidget::pane{border:1px solid #444;background-color:#2B2B2B;"
            "border-radius:4px;top:-1px}"
            "QTabBar::tab{background-color:#3C3C3C;color:#CCC;padding:6px 16px;"
            "border:1px solid #444;border-bottom:none;"
            "border-top-left-radius:4px;border-top-right-radius:4px;"
            "font-size:10px}"
            "QTabBar::tab:selected{background-color:#2B2B2B;color:#FFF;"
            "border-color:#2196F3}"
            "QTabBar::tab:hover{background-color:#4A4A4A}")

        # ---- Cylinder tab ----
        cyl_tab = QtWidgets.QWidget()
        cyl_tab_lo = QtWidgets.QVBoxLayout(cyl_tab)
        cyl_tab_lo.setContentsMargins(0, 0, 0, 0)
        cyl_tab_lo.setSpacing(0)

        cyl_scroll = QtWidgets.QScrollArea()
        cyl_scroll.setWidgetResizable(True)
        cyl_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        cyl_scroll_w = QtWidgets.QWidget()
        scroll_lo = QtWidgets.QVBoxLayout(cyl_scroll_w)
        scroll_lo.setContentsMargins(4, 4, 4, 4)
        scroll_lo.setSpacing(8)

        # Cleanup group
        _cc_build_group(self, scroll_lo)
        # Change-sides group
        _rs_build_group(self, scroll_lo)

        scroll_lo.addStretch()
        cyl_scroll.setWidget(cyl_scroll_w)
        cyl_tab_lo.addWidget(cyl_scroll)

        self._tabs.addTab(cyl_tab, tr("tab_cylinder"))
        main_lo.addWidget(self._tabs)

        # ---- Status bar ----
        self._status_bar = QtWidgets.QLabel(tr("status_ready"))
        self._status_bar.setStyleSheet(
            "color:#AAA;font-size:10px;padding:4px 6px;"
            "background-color:#2B2B2B;border-top:1px solid #444")
        self._status_bar.setMinimumHeight(22)
        main_lo.addWidget(self._status_bar)

    # ------------------------------------------------------------------
    def _toggle_lang(self):
        global _current_lang
        _current_lang = LANG_JP if _current_lang == LANG_EN else LANG_EN
        self._refresh_labels()

    def _refresh_labels(self):
        self._title_lbl.setText(
            u"<b>{0}</b> <span style='color:#888;font-size:10px'>v{1}</span>".format(
                tr("window_title"), VERSION))
        self.setWindowTitle(tr("window_title"))
        self._lang_btn.setText(tr("btn_lang"))
        self._status_bar.setText(tr("status_ready"))
        try:
            self._tabs.setTabText(0, tr("tab_cylinder"))
        except Exception:
            pass
        _cc_refresh_labels(self)
        _rs_refresh_labels(self)

    # ------------------------------------------------------------------
    def _open_help(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(tr("help_title"))
        dlg.setWindowFlags(dlg.windowFlags() | QtCore.Qt.Tool)
        dlg.setMinimumSize(560, 520)
        dlg.setStyleSheet(
            "QDialog{background-color:#333}"
            "QTextBrowser{background-color:#2B2B2B;color:#EEE;"
            "border:1px solid #444;padding:8px;font-size:11px}"
            "QTabWidget::pane{border:1px solid #444;background:#2B2B2B;top:-1px}"
            "QTabBar::tab{background:#3C3C3C;color:#BBB;padding:6px 14px;"
            "border:1px solid #444;border-bottom:none;margin-right:1px;"
            "font-size:11px}"
            "QTabBar::tab:selected{background:#2B2B2B;color:#EEE;font-weight:bold}")
        lo = QtWidgets.QVBoxLayout(dlg)
        lo.setContentsMargins(8, 8, 8, 8)
        lo.setSpacing(6)
        tabs = QtWidgets.QTabWidget()
        tb = QtWidgets.QTextBrowser()
        tb.setHtml(tr("help_body_cylinder"))
        tb.setOpenExternalLinks(True)
        tabs.addTab(tb, tr("tab_cylinder"))
        lo.addWidget(tabs)
        btn_lo = QtWidgets.QHBoxLayout()
        btn_lo.addStretch()
        close = _mkbtn(tr("btn_close"), 26, "#555", "#444")
        close.clicked.connect(dlg.accept)
        btn_lo.addWidget(close)
        lo.addLayout(btn_lo)
        dlg.exec_()

    # ------------------------------------------------------------------
    def _on_reload(self):
        global _saved_geometry, _saved_lang
        geo = self.geometry()
        _saved_geometry = (geo.x(), geo.y(), geo.width(), geo.height())
        _saved_lang = _current_lang
        self.close()

        mn = self.__class__.__module__
        mod = sys.modules.get(mn)

        if mod is None or mn == "__main__":
            for name, m in list(sys.modules.items()):
                if name == "__main__":
                    continue
                f = getattr(m, "__file__", None)
                if f and "DW_Remesher" in f:
                    mn = name
                    mod = m
                    break

        if mod is not None and mn != "__main__":
            _reload(mod)
            mod._saved_geometry = _saved_geometry
            mod._saved_lang = _saved_lang
            mod.show()
        else:
            if "DW_Remesher" in sys.modules:
                mod = sys.modules["DW_Remesher"]
                _reload(mod)
                mod._saved_geometry = _saved_geometry
                mod._saved_lang = _saved_lang
                mod.show()

    # ------------------------------------------------------------------
    def _on_check_update(self):
        result = check_for_updates(silent=False)
        self._set_update_btn_state(result)

    def _set_update_btn_state(self, state):
        if state == "newer_available":
            bg = "#D32F2F"
            hv = "#E53935"
            tip = tr("btn_update") + " (NEW!)"
        elif state == "latest":
            bg = "#1976D2"
            hv = "#2196F3"
            tip = tr("btn_update") + " (up to date)"
        else:
            bg = "#555"
            hv = "#9C27B0"
            tip = tr("btn_update")
        self._update_btn.setStyleSheet(
            "QPushButton{{background-color:{0};color:#EEE;"
            "border:1px solid #777;border-radius:3px;font-size:12px}}"
            "QPushButton:hover{{background-color:{1}}}".format(bg, hv))
        self._update_btn.setToolTip(tip)

    def _startup_version_check(self):
        try:
            state = check_for_updates(silent=True)
            self._set_update_btn_state(state)
        except Exception:
            self._set_update_btn_state("unknown")


def _url_read(url, timeout=10):
    """Read a URL and return the decoded string. Py2/3 compatible."""
    if PY2:
        import urllib2
        resp = urllib2.urlopen(url, timeout=timeout)
        data = resp.read()
    else:
        import urllib.request
        resp = urllib.request.urlopen(url, timeout=timeout)
        data = resp.read()
    if isinstance(data, bytes):
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("utf-8", errors="replace")
    return data


def _extract_remote_version(source_text):
    """Extract 'VERSION = "..."' line from source code."""
    import re
    m = re.search(r'^VERSION\s*=\s*"([^"]+)"', source_text, re.MULTILINE)
    return m.group(1) if m else None


def check_for_updates(silent=False):
    """
    Check GitHub for a newer version.

    silent=False (default, interactive):
        Shows dialogs. If a newer version is available, asks the user
        to download and installs it to Maya scripts folder.

    silent=True (background check at startup):
        Never shows any dialog. Only returns a state string.

    Returns:
        'latest'          — local version matches remote (up to date)
        'newer_available' — remote has a newer version
        'unknown'         — offline, parse error, or Maya not available
    """
    if not MAYA_AVAILABLE:
        return "unknown"

    # Fetch remote source
    try:
        source = _url_read(_GITHUB_RAW_URL, timeout=5 if silent else 10)
    except Exception as e:
        if not silent:
            QtWidgets.QMessageBox.warning(
                None, "Update Check",
                "Failed to connect to GitHub.\n{0}".format(str(e)))
        return "unknown"

    remote_ver = _extract_remote_version(source)
    if not remote_ver:
        if not silent:
            QtWidgets.QMessageBox.warning(
                None, "Update Check",
                "Could not read remote version.")
        return "unknown"

    local_ver = VERSION

    if remote_ver == local_ver:
        if not silent:
            QtWidgets.QMessageBox.information(
                None, "Update Check",
                u"\u6700\u65b0\u7248\u3067\u3059\u3002\n"
                u"Version: {0}".format(local_ver))
        return "latest"

    # Lexical comparison works for YYYY.MM.DD.HHMM format
    is_newer = remote_ver > local_ver

    if not is_newer:
        # Local is ahead of remote (dev state). Treat as up to date.
        if not silent:
            msg = (u"\u30ed\u30fc\u30ab\u30eb\u7248\u306e\u65b9\u304c\u65b0"
                   u"\u3057\u3044\u3088\u3046\u3067\u3059\u3002\n\n"
                   u"Local:  {0}\nRemote: {1}").format(local_ver, remote_ver)
            QtWidgets.QMessageBox.information(None, "Update Check", msg)
        return "latest"

    # A newer remote version exists
    if silent:
        return "newer_available"

    # Interactive: ask to download
    msg = (u"\u65b0\u3057\u3044\u30d0\u30fc\u30b8\u30e7\u30f3\u304c\u3042"
           u"\u308a\u307e\u3059\u3002\n\n"
           u"Local:  {0}\nRemote: {1}\n\n"
           u"\u30c0\u30a6\u30f3\u30ed\u30fc\u30c9\u3057\u3066\u66f4\u65b0"
           u"\u3057\u307e\u3059\u304b\uff1f").format(local_ver, remote_ver)
    reply = QtWidgets.QMessageBox.question(
        None, "Update Check", msg,
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    if reply != QtWidgets.QMessageBox.Yes:
        return "newer_available"

    # Save to Maya scripts folder
    try:
        scripts_dir = cmds.internalVar(userScriptDir=True)
        if scripts_dir.endswith("/") or scripts_dir.endswith("\\"):
            scripts_dir = scripts_dir[:-1]
        dest = os.path.join(scripts_dir, "DW_Remesher.py")

        # Backup existing
        if os.path.exists(dest):
            bak = dest + ".bak"
            if os.path.exists(bak):
                try:
                    os.remove(bak)
                except Exception:
                    pass
            try:
                os.rename(dest, bak)
            except Exception:
                pass

        if PY2:
            with open(dest, "wb") as f:
                f.write(source.encode("utf-8"))
        else:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(source)

        done_msg = (u"v{0} \u306b\u66f4\u65b0\u3057\u307e\u3057\u305f\u3002\n\n"
                    u"\u4fdd\u5b58\u5148: {1}\n\n"
                    u"\u30c4\u30fc\u30eb\u3092\u518d\u8d77\u52d5\u3057\u3066"
                    u"\u304f\u3060\u3055\u3044\u3002\n"
                    u"(\u30e1\u30a4\u30f3\u30a6\u30a3\u30f3\u30c9\u30a6\u306e"
                    u"\u30ea\u30ed\u30fc\u30c9\u30dc\u30bf\u30f3\u3092\u30af"
                    u"\u30ea\u30c3\u30af)").format(remote_ver, dest)
        QtWidgets.QMessageBox.information(None, "Update Check", done_msg)
        return "latest"  # after update, local matches remote
    except Exception as e:
        QtWidgets.QMessageBox.warning(
            None, "Update Check",
            "Failed to save update.\n{0}".format(str(e)))
        return "newer_available"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def show():
    global _saved_geometry, _saved_lang, _current_lang

    # Close existing instance
    for w in QtWidgets.QApplication.allWidgets():
        if isinstance(w, RemesherToolWindow):
            w.close()
            w.deleteLater()

    if _saved_lang:
        _current_lang = _saved_lang
        _saved_lang = None

    win = RemesherToolWindow()
    win.show()

    # Background version check. Delayed so the UI shows immediately
    # and the user never waits for the network. Never blocks or fails.
    try:
        QtCore.QTimer.singleShot(500, win._startup_version_check)
    except Exception:
        pass

    return win


if __name__ == "__main__":
    # Standalone test (outside Maya)
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    win = show()
    app.exec_()


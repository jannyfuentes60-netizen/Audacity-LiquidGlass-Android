#include <QtGui/private/qhighdpiscaling_p.h>
#include <qpa/qplatformwindow.h>

// Compile-only probe: verifies the exact Qt private/QPA headers required by
// KDDockWidgets' QtQuick backend are available for the Android target.
static QPlatformWindow *android_qpa_header_probe(QPlatformWindow *window)
{
    (void)sizeof(QHighDpiScaling *);
    return window;
}

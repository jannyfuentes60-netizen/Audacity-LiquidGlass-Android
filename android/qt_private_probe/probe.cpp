#include <QtGui/private/qhighdpiscaling_p.h>
#include <qpa/qplatformwindow.h>

// Compile-only probe for the private QtGui and QPA headers used by
// KDDockWidgets' QtQuick backend.
int qt_android_private_header_probe()
{
    return 0;
}

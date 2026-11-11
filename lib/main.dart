import 'package:flutter/widgets.dart';
import 'package:liqkit_ui/liqkit_ui.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await LiqGlassSurface.precacheShader();
  runApp(const AudacityMobileApp());
}

class AudacityMobileApp extends StatelessWidget {
  const AudacityMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const LiqApp(
      title: 'Audacity',
      light: LiqThemeData.light,
      dark: LiqThemeData.dark,
      themeMode: LiqThemeMode.dark,
      home: LibraryHome(),
    );
  }
}

class LibraryHome extends StatefulWidget {
  const LibraryHome({super.key});

  @override
  State<LibraryHome> createState() => _LibraryHomeState();
}

class _LibraryHomeState extends State<LibraryHome> {
  int _selectedTab = 0;

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.ltr,
      child: ColoredBox(
        color: const Color(0xFF090B10),
        child: Stack(
          children: [
            const Positioned.fill(child: _AmbientBackground()),
            SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 18, 20, 18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('AUDACITY', style: TextStyle(
                                color: Color(0xFF8E9AAA),
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 2.4,
                              )),
                              SizedBox(height: 5),
                              Text('Tu biblioteca', style: TextStyle(
                                color: Color(0xFFF5F7FA),
                                fontSize: 30,
                                fontWeight: FontWeight.w700,
                                letterSpacing: -1.1,
                              )),
                            ],
                          ),
                        ),
                        _GlassButton(
                          icon: '⚙',
                          label: 'Ajustes',
                          onTap: () => _showMessage('Los ajustes estarán disponibles en una siguiente etapa.'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 26),
                    LiqGlassSurface(
                      tint: LiqGlassTint.dark,
                      borderRadius: BorderRadius.circular(24),
                      padding: const EdgeInsets.all(18),
                      child: const Row(
                        children: [
                          _WaveMark(),
                          SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Audacity 3.7.8', style: TextStyle(
                                  color: Color(0xFFF4F6FA),
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                )),
                                SizedBox(height: 4),
                                Text('Proyecto Android · Liquid Glass', style: TextStyle(
                                  color: Color(0xFF9BA8B8),
                                  fontSize: 12,
                                )),
                              ],
                            ),
                          ),
                          Text('PREVIEW', style: TextStyle(
                            color: Color(0xFF8BC5FF),
                            fontSize: 9,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1.2,
                          )),
                        ],
                      ),
                    ),
                    const SizedBox(height: 28),
                    Row(
                      children: [
                        const Expanded(child: Text('Archivos de audio', style: TextStyle(
                          color: Color(0xFFF4F6FA),
                          fontSize: 19,
                          fontWeight: FontWeight.w700,
                        ))),
                        Text('0 archivos', style: TextStyle(
                          color: Color(0xFF8D99A8),
                          fontSize: 12,
                        )),
                      ],
                    ),
                    const SizedBox(height: 14),
                    Expanded(
                      child: Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const _LibraryGlyph(),
                            const SizedBox(height: 18),
                            const Text('Tu música aparecerá aquí', style: TextStyle(
                              color: Color(0xFFF0F3F8),
                              fontSize: 17,
                              fontWeight: FontWeight.w600,
                            )),
                            const SizedBox(height: 7),
                            const Text(
                              'Audacity buscará los audios a los que\nle hayas dado permiso en tu dispositivo.',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                color: Color(0xFF929EAD),
                                fontSize: 13,
                                height: 1.5,
                              ),
                            ),
                            const SizedBox(height: 20),
                            _GlassButton(
                              icon: '＋',
                              label: 'Conectar biblioteca',
                              primary: true,
                              onTap: () => _showMessage(
                                'La conexión con MediaStore y el permiso de audio se implementarán en el siguiente hito.',
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    LiqGlassSurface(
                      tint: LiqGlassTint.dark,
                      borderRadius: BorderRadius.circular(22),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      child: Row(
                        children: [
                          _TabButton(
                            icon: '♫',
                            label: 'Biblioteca',
                            selected: _selectedTab == 0,
                            onTap: () => setState(() => _selectedTab = 0),
                          ),
                          _TabButton(
                            icon: '▤',
                            label: 'Proyectos',
                            selected: _selectedTab == 1,
                            onTap: () {
                              setState(() => _selectedTab = 1);
                              _showMessage('La lista de proyectos se añadirá al integrar el motor.');
                            },
                          ),
                          _TabButton(
                            icon: '◉',
                            label: 'Herramientas',
                            selected: _selectedTab == 2,
                            onTap: () {
                              setState(() => _selectedTab = 2);
                              _showMessage('Las herramientas de edición llegarán con el motor nativo.');
                            },
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showMessage(String message) {
    late final OverlayEntry entry;
    entry = OverlayEntry(
      builder: (overlayContext) => Positioned.fill(
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: () => entry.remove(),
          child: ColoredBox(
            color: const Color(0x99000000),
            child: Center(
              child: GestureDetector(
                onTap: () {},
                child: Padding(
                  padding: const EdgeInsets.all(28),
                  child: LiqGlassSurface(
                    tint: LiqGlassTint.dark,
                    borderRadius: BorderRadius.circular(24),
                    padding: const EdgeInsets.all(22),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('En desarrollo', style: TextStyle(
                          color: Color(0xFFF4F6FA),
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        )),
                        const SizedBox(height: 10),
                        Text(message, style: const TextStyle(
                          color: Color(0xFFB7C1CE),
                          fontSize: 14,
                          height: 1.45,
                        )),
                        const SizedBox(height: 18),
                        Align(
                          alignment: Alignment.centerRight,
                          child: GestureDetector(
                            onTap: () => entry.remove(),
                            child: const Text('Entendido', style: TextStyle(
                              color: Color(0xFF8BC5FF),
                              fontWeight: FontWeight.w700,
                            )),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
    Overlay.of(context).insert(entry);
  }
}

class _AmbientBackground extends StatelessWidget {
  const _AmbientBackground();

  @override
  Widget build(BuildContext context) => const DecoratedBox(
    decoration: BoxDecoration(
      gradient: RadialGradient(
        center: Alignment(-0.85, -0.85),
        radius: 1.25,
        colors: [Color(0xFF18334B), Color(0xFF0C111A), Color(0xFF090B10)],
        stops: [0, 0.43, 1],
      ),
    ),
  );
}

class _GlassButton extends StatelessWidget {
  const _GlassButton({required this.icon, required this.label, required this.onTap, this.primary = false});
  final String icon;
  final String label;
  final VoidCallback onTap;
  final bool primary;

  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    child: LiqGlassSurface(
      tint: LiqGlassTint.dark,
      borderRadius: BorderRadius.circular(18),
      baseFill: primary ? const Color(0xFF245A86) : null,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Text(icon, style: const TextStyle(color: Color(0xFFEAF4FF), fontSize: 16)),
        const SizedBox(width: 8),
        Text(label, style: const TextStyle(color: Color(0xFFEAF4FF), fontSize: 12, fontWeight: FontWeight.w600)),
      ]),
    ),
  );
}

class _TabButton extends StatelessWidget {
  const _TabButton({required this.icon, required this.label, required this.selected, required this.onTap});
  final String icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Expanded(
    child: GestureDetector(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 9),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(icon, style: TextStyle(color: selected ? const Color(0xFF8BC5FF) : const Color(0xFF929EAD), fontSize: 18)),
          const SizedBox(height: 4),
          Text(label, style: TextStyle(color: selected ? const Color(0xFFF4F6FA) : const Color(0xFF929EAD), fontSize: 10, fontWeight: selected ? FontWeight.w700 : FontWeight.w500)),
        ]),
      ),
    ),
  );
}

class _WaveMark extends StatelessWidget {
  const _WaveMark();

  @override
  Widget build(BuildContext context) => Container(
    width: 44,
    height: 44,
    decoration: BoxDecoration(
      color: const Color(0xFF173A58),
      borderRadius: BorderRadius.circular(15),
    ),
    child: const Center(child: Text('∿', style: TextStyle(color: Color(0xFF9ED3FF), fontSize: 31, fontWeight: FontWeight.w700))),
  );
}

class _LibraryGlyph extends StatelessWidget {
  const _LibraryGlyph();

  @override
  Widget build(BuildContext context) => LiqGlassSurface(
    tint: LiqGlassTint.dark,
    borderRadius: BorderRadius.circular(30),
    padding: const EdgeInsets.all(24),
    child: const Text('♫', style: TextStyle(color: Color(0xFF9ED3FF), fontSize: 42)),
  );
}

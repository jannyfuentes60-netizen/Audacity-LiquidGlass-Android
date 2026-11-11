import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:liqkit_ui/liqkit_ui.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await LiqGlassSurface.precacheShader();
  runApp(const AudacityMobileApp());
}

class AudacityMobileApp extends StatelessWidget {
  const AudacityMobileApp({super.key});
  @override
  Widget build(BuildContext context) => const LiqApp(
    title: 'Audacity', light: LiqThemeData.light, dark: LiqThemeData.dark,
    themeMode: LiqThemeMode.dark, home: AudacityWorkspace(),
  );
}

class AudacityWorkspace extends StatefulWidget {
  const AudacityWorkspace({super.key});
  @override
  State<AudacityWorkspace> createState() => _AudacityWorkspaceState();
}

class _AudacityWorkspaceState extends State<AudacityWorkspace> {
  int _tab = 0, _tool = 0, _selectedTrack = 0, _trackCount = 1;
  double _zoom = 1;
  bool _playing = false;
  static const _tools = [('↖', 'Selección'), ('✂', 'Cortar'), ('⌁', 'Envolvente'), ('⌖', 'Desplazar'), ('⌕', 'Zoom')];

  void _notice(String text) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(
    content: Text(text), behavior: SnackBarBehavior.floating,
    backgroundColor: const Color(0xFF263746),
  ));

  @override
  Widget build(BuildContext context) {
    const ink = Color(0xFFF4F7FB), muted = Color(0xFF9AAABD), accent = Color(0xFF9DEBFA);
    return Theme(
      data: Theme.of(context).copyWith(
        scaffoldBackgroundColor: const Color(0xFF080C12),
        colorScheme: const ColorScheme.dark(primary: accent, surface: Color(0xFF17212C)),
      ),
      child: Scaffold(
        body: Stack(children: [
          const Positioned.fill(child: _AmbientBackground()),
          SafeArea(child: Column(children: [
            _topBar(ink, muted, accent),
            Expanded(child: GestureDetector(
              onHorizontalDragEnd: (d) {
                if ((d.primaryVelocity ?? 0) < -250) setState(() => _tab = (_tab + 1).clamp(0, 2));
                if ((d.primaryVelocity ?? 0) > 250) setState(() => _tab = (_tab - 1).clamp(0, 2));
              },
              child: _tab == 0 ? _editor(ink, muted, accent) : _tab == 1
                ? _projects(ink, muted, accent) : _settings(ink, muted, accent),
            )),
            _bottomBar(ink, muted, accent),
          ])),
        ]),
      ),
    );
  }

  Widget _topBar(Color ink, Color muted, Color accent) => Padding(
    padding: const EdgeInsets.fromLTRB(18, 8, 18, 10),
    child: Row(children: [
      _glassIcon('∿', accent, size: 42), const SizedBox(width: 12),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('AUDACITY', style: TextStyle(color: muted, fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 2.1)),
        Text(_tab == 0 ? 'Editor multipista' : _tab == 1 ? 'Proyectos' : 'Ajustes',
          style: TextStyle(color: ink, fontSize: 20, fontWeight: FontWeight.w700, letterSpacing: -.5)),
      ])),
      _glassIcon('↶', muted, onTap: () => _notice('Deshacer se conectará al motor de edición.')),
      const SizedBox(width: 7),
      _glassIcon('↷', muted, onTap: () => _notice('Rehacer se conectará al motor de edición.')),
      const SizedBox(width: 7),
      _glassIcon('⋯', ink, onTap: () => _notice('Menú del proyecto')),
    ]),
  );

  Widget _editor(Color ink, Color muted, Color accent) => Column(children: [
    Padding(padding: const EdgeInsets.fromLTRB(16, 2, 16, 10), child: Row(children: [
      Expanded(child: _projectPill('Proyecto sin guardar', '44.1 kHz · Estéreo', muted, ink)),
      const SizedBox(width: 8),
      _glassIcon('＋', accent, onTap: () => setState(() { _trackCount++; _selectedTrack = _trackCount - 1; })),
      const SizedBox(width: 8),
      _glassIcon('⇧', accent, onTap: () => _notice('La importación se conectará al acceso nativo a archivos.')),
    ])),
    _toolStrip(ink, muted, accent),
    const SizedBox(height: 10),
    _transport(ink, muted, accent),
    const SizedBox(height: 10),
    Expanded(child: Container(
      margin: const EdgeInsets.fromLTRB(12, 0, 12, 8),
      decoration: BoxDecoration(color: const Color(0x99121B26), borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.white.withValues(alpha: .10))),
      child: Column(children: [
        _timelineRuler(muted),
        Expanded(child: ListView.builder(
          padding: const EdgeInsets.fromLTRB(9, 8, 9, 14),
          itemCount: _trackCount,
          itemBuilder: (context, index) => _track(index, ink, muted, accent),
        )),
      ]),
    )),
    _zoomBar(muted, accent),
  ]);

  Widget _projectPill(String title, String subtitle, Color muted, Color ink) => LiqGlassSurface(
    tint: LiqGlassTint.dark, borderRadius: BorderRadius.circular(17),
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
    child: Row(children: [
      const Icon(Icons.graphic_eq, color: Color(0xFF9DEBFA), size: 20), const SizedBox(width: 10),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, maxLines: 1, overflow: TextOverflow.ellipsis,
          style: TextStyle(color: ink, fontSize: 12, fontWeight: FontWeight.w700)),
        Text(subtitle, style: TextStyle(color: muted, fontSize: 10)),
      ])),
    ]),
  );

  Widget _toolStrip(Color ink, Color muted, Color accent) => SizedBox(height: 60, child: ListView.separated(
    padding: const EdgeInsets.symmetric(horizontal: 15), scrollDirection: Axis.horizontal,
    itemCount: _tools.length, separatorBuilder: (_, __) => const SizedBox(width: 8),
    itemBuilder: (context, index) {
      final selected = _tool == index;
      return GestureDetector(onTap: () => setState(() => _tool = index), child: LiqGlassSurface(
        tint: LiqGlassTint.dark, baseFill: selected ? const Color(0xFF25485A) : null,
        borderRadius: BorderRadius.circular(17), padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 8),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Text(_tools[index].$1, style: TextStyle(color: selected ? accent : ink, fontSize: 19)),
          Text(_tools[index].$2, style: TextStyle(color: selected ? accent : muted, fontSize: 9)),
        ]),
      ));
    },
  ));

  Widget _transport(Color ink, Color muted, Color accent) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 16),
    child: LiqGlassSurface(tint: LiqGlassTint.dark, borderRadius: BorderRadius.circular(22),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
      child: Row(children: [
        _transportButton('⏮', muted, () {}),
        _transportButton(_playing ? 'Ⅱ' : '▶', accent, () => setState(() => _playing = !_playing), large: true),
        _transportButton('⏹', muted, () => setState(() => _playing = false)),
        _transportButton('⏺', const Color(0xFFFF777D), () => _notice('La grabación requiere el motor de audio nativo.')),
        const Spacer(),
        Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Text('00:00.000', style: TextStyle(color: ink, fontSize: 14, fontWeight: FontWeight.w700)),
          Text('00:00.000', style: TextStyle(color: muted, fontSize: 9)),
        ]),
      ]),
    ),
  );

  Widget _transportButton(String glyph, Color color, VoidCallback onTap, {bool large = false}) => GestureDetector(
    onTap: onTap,
    child: Container(width: large ? 43 : 35, height: large ? 43 : 35,
      margin: const EdgeInsets.symmetric(horizontal: 3),
      decoration: BoxDecoration(shape: BoxShape.circle,
        color: large ? const Color(0xFF2C6477) : Colors.white.withValues(alpha: .055),
        border: Border.all(color: Colors.white.withValues(alpha: .12))),
      alignment: Alignment.center, child: Text(glyph, style: TextStyle(color: color, fontSize: large ? 18 : 15)),
    ),
  );

  Widget _timelineRuler(Color muted) => SizedBox(height: 36, child: Row(children: [
    const SizedBox(width: 105),
    Expanded(child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: List.generate(6, (i) => Text('${i * 5}s', style: TextStyle(color: muted, fontSize: 9))))),
  ]));

  Widget _track(int index, Color ink, Color muted, Color accent) {
    final selected = _selectedTrack == index;
    return GestureDetector(onTap: () => setState(() => _selectedTrack = index),
      child: Container(height: 112, margin: const EdgeInsets.only(bottom: 9),
        decoration: BoxDecoration(
          color: selected ? const Color(0xFF1C3340) : const Color(0xFF151F2A),
          borderRadius: BorderRadius.circular(15),
          border: Border.all(color: selected ? accent.withValues(alpha: .5) : Colors.white.withValues(alpha: .07))),
        child: Row(children: [
          SizedBox(width: 100, child: Padding(padding: const EdgeInsets.all(9),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Pista ${index + 1}', style: TextStyle(color: ink, fontSize: 11, fontWeight: FontWeight.w700)),
              const Spacer(),
              Row(children: [_miniAction('M', muted), const SizedBox(width: 5), _miniAction('S', muted),
                const Spacer(), Icon(Icons.more_horiz, color: muted, size: 17)]),
              const SizedBox(height: 5),
              Row(children: [Icon(Icons.volume_down, color: muted, size: 12),
                Expanded(child: Container(height: 3, decoration: BoxDecoration(color: muted.withValues(alpha: .25),
                  borderRadius: BorderRadius.circular(3))))]),
            ]),
          )),
          Expanded(child: ClipRRect(
            borderRadius: const BorderRadius.horizontal(right: Radius.circular(14)),
            child: CustomPaint(painter: _WaveformPainter(color: selected ? accent : const Color(0xFF6C9FB2), zoom: _zoom),
              child: const SizedBox.expand()),
          )),
        ]),
      ),
    );
  }

  Widget _miniAction(String label, Color muted) => Container(width: 22, height: 19,
    alignment: Alignment.center, decoration: BoxDecoration(color: Colors.white.withValues(alpha: .07),
      borderRadius: BorderRadius.circular(6)),
    child: Text(label, style: TextStyle(color: muted, fontSize: 9, fontWeight: FontWeight.bold)));

  Widget _zoomBar(Color muted, Color accent) => Padding(
    padding: const EdgeInsets.fromLTRB(18, 0, 18, 9),
    child: Row(children: [
      Text('PISTAS: $_trackCount', style: TextStyle(color: muted, fontSize: 9, letterSpacing: 1)),
      const Spacer(),
      GestureDetector(onTap: () => setState(() => _zoom = (_zoom / 1.2).clamp(.5, 3)),
        child: Icon(Icons.remove_circle_outline, color: muted, size: 20)),
      const SizedBox(width: 12),
      Text('${(_zoom * 100).round()}%', style: TextStyle(color: accent, fontSize: 10)),
      const SizedBox(width: 12),
      GestureDetector(onTap: () => setState(() => _zoom = (_zoom * 1.2).clamp(.5, 3)),
        child: Icon(Icons.add_circle_outline, color: muted, size: 20)),
    ]),
  );

  Widget _projects(Color ink, Color muted, Color accent) => Center(child: Padding(
    padding: const EdgeInsets.all(28),
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      Icon(Icons.folder_open_rounded, color: accent, size: 42), const SizedBox(height: 14),
      Text('Proyectos de Audacity', style: TextStyle(color: ink, fontSize: 19, fontWeight: FontWeight.w700)),
      const SizedBox(height: 7),
      Text('Aquí aparecerán tus sesiones guardadas al integrar el sistema de proyectos.',
        textAlign: TextAlign.center, style: TextStyle(color: muted, fontSize: 12, height: 1.5)),
    ]),
  ));

  Widget _settings(Color ink, Color muted, Color accent) => ListView(padding: const EdgeInsets.all(20), children: [
    Text('Interfaz', style: TextStyle(color: ink, fontSize: 18, fontWeight: FontWeight.w700)),
    const SizedBox(height: 12),
    _settingRow('Apariencia', 'Oscura · Liquid Glass', muted, ink),
    const SizedBox(height: 14),
    Text('Audio', style: TextStyle(color: ink, fontSize: 18, fontWeight: FontWeight.w700)),
    const SizedBox(height: 8),
    _settingRow('Dispositivos de entrada y salida', 'Pendiente de integrar', muted, ink),
    _settingRow('Frecuencia de muestreo', '44.1 / 48 / 96 kHz', muted, ink),
    _settingRow('Calidad de exportación', 'Pendiente de integrar', muted, ink),
  ]);

  Widget _settingRow(String title, String subtitle, Color muted, Color ink) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: LiqGlassSurface(tint: LiqGlassTint.dark, borderRadius: BorderRadius.circular(16),
      padding: const EdgeInsets.all(16),
      child: Row(children: [
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: TextStyle(color: ink, fontSize: 13)),
          Text(subtitle, style: TextStyle(color: muted, fontSize: 10)),
        ])),
        Icon(Icons.chevron_right, color: muted),
      ])),
  );

  Widget _bottomBar(Color ink, Color muted, Color accent) {
    const labels = ['Editor', 'Proyectos', 'Ajustes'];
    const icons = [Icons.graphic_eq, Icons.folder_open, Icons.tune];
    return Padding(padding: const EdgeInsets.fromLTRB(16, 2, 16, 10),
      child: LiqGlassSurface(tint: LiqGlassTint.dark, borderRadius: BorderRadius.circular(24),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
        child: Row(children: List.generate(3, (i) => Expanded(child: GestureDetector(
          onTap: () => setState(() => _tab = i),
          child: AnimatedContainer(duration: const Duration(milliseconds: 180),
            padding: const EdgeInsets.symmetric(vertical: 8),
            decoration: BoxDecoration(color: _tab == i ? const Color(0xFF294B5C).withValues(alpha: .8) : Colors.transparent,
              borderRadius: BorderRadius.circular(17)),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Icon(icons[i], color: _tab == i ? accent : muted, size: 19),
              const SizedBox(height: 3),
              Text(labels[i], style: TextStyle(color: _tab == i ? ink : muted, fontSize: 9,
                fontWeight: _tab == i ? FontWeight.w700 : FontWeight.w500)),
            ]),
          ),
        )))),
      ),
    );
  }

  Widget _glassIcon(String glyph, Color color, {VoidCallback? onTap, double size = 38}) => GestureDetector(
    onTap: onTap,
    child: LiqGlassSurface(tint: LiqGlassTint.dark, borderRadius: BorderRadius.circular(size * .38),
      padding: EdgeInsets.all(size * .20),
      child: SizedBox(width: size * .55, height: size * .55,
        child: Center(child: Text(glyph, style: TextStyle(color: color, fontSize: size * .48)))),
    ),
  );
}

class _AmbientBackground extends StatelessWidget {
  const _AmbientBackground();
  @override
  Widget build(BuildContext context) => const DecoratedBox(
    decoration: BoxDecoration(gradient: RadialGradient(
      center: Alignment(-.85, -.9), radius: 1.35,
      colors: [Color(0xFF17394B), Color(0xFF0D1620), Color(0xFF080C12)],
      stops: [0, .42, 1],
    )),
  );
}

class _WaveformPainter extends CustomPainter {
  const _WaveformPainter({required this.color, required this.zoom});
  final Color color;
  final double zoom;
  @override
  void paint(Canvas canvas, Size size) {
    final center = size.height / 2;
    final paint = Paint()..color = color.withValues(alpha: .78)..strokeWidth = 2..strokeCap = StrokeCap.round;
    final step = (4 / zoom).clamp(1.5, 7.0);
    for (double x = 3; x < size.width; x += step) {
      final envelope = .22 + .78 * (.5 + .5 * math.sin(x * .025));
      final wave = (math.sin(x * .19) * .45 + math.sin(x * .071) * .35 + math.cos(x * .31) * .2).abs();
      final half = (4 + wave * center * .78) * envelope;
      canvas.drawLine(Offset(x, center - half), Offset(x, center + half), paint);
    }
    final grid = Paint()..color = Colors.white.withValues(alpha: .08)..strokeWidth = 1;
    for (double x = 0; x < size.width; x += 60) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), grid);
    }
  }
  @override
  bool shouldRepaint(covariant _WaveformPainter oldDelegate) => oldDelegate.color != color || oldDelegate.zoom != zoom;
}

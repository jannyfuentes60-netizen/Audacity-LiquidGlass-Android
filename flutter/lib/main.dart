import 'dart:io';

import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import 'package:liquid_glass_widgets/liquid_glass_widgets.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _runtime = MethodChannel('com.djfaraon.audacity/runtime');
const _qualityKey = 'library_glass_quality_v1';

enum GlassTier { premium, standard, minimal }

extension GlassTierLabel on GlassTier {
  String get label => switch (this) {
        GlassTier.premium => 'Premium',
        GlassTier.standard => 'Estándar',
        GlassTier.minimal => 'Ligera',
      };

  String get description => switch (this) {
        GlassTier.premium => 'Refacción, iluminación y lentes Liquid Glass completos.',
        GlassTier.standard => 'Efectos equilibrados para mantener la biblioteca fluida.',
        GlassTier.minimal => 'Efectos reducidos para dispositivos con recursos limitados.',
      };
}

class DeviceAssessment {
  const DeviceAssessment({
    required this.model,
    required this.ramGb,
    required this.cores,
    required this.lowRam,
    required this.androidSdk,
    required this.recommendation,
    required this.reason,
  });

  final String model;
  final int ramGb;
  final int cores;
  final bool lowRam;
  final int androidSdk;
  final GlassTier recommendation;
  final String reason;

  static Future<DeviceAssessment> run() async {
    if (!Platform.isAndroid) {
      return const DeviceAssessment(
        model: 'Dispositivo no Android',
        ramGb: 0,
        cores: 0,
        lowRam: false,
        androidSdk: 0,
        recommendation: GlassTier.standard,
        reason: 'Se usa una configuración equilibrada mientras se completa el diagnóstico de esta plataforma.',
      );
    }

    final info = await DeviceInfoPlugin().androidInfo;
    final ram = info.physicalRamSize;
    final cores = info.numberOfProcessors;
    final lowRam = info.isLowRamDevice;
    final sdk = info.version.sdkInt;

    // This is deliberately conservative: device_info_plus does not expose a
    // reliable GPU benchmark. Premium is recommended only when the device
    // has sufficient RAM/CPU and Android does not classify it as low-RAM.
    final GlassTier tier;
    final String reason;
    if (!lowRam && ram >= 8 && cores >= 8 && sdk >= 29) {
      tier = GlassTier.premium;
      reason = 'Memoria, procesador y versión de Android indican margen para probar la calidad máxima.';
    } else if (!lowRam && ram >= 4 && cores >= 6 && sdk >= 26) {
      tier = GlassTier.standard;
      reason = 'El dispositivo puede usar efectos Liquid Glass, pero conviene reservar Premium para equipos con más margen gráfico.';
    } else {
      tier = GlassTier.minimal;
      reason = 'El sistema reporta recursos limitados; se prioriza la fluidez de la biblioteca.';
    }

    return DeviceAssessment(
      model: info.model,
      ramGb: ram,
      cores: cores,
      lowRam: lowRam,
      androidSdk: sdk,
      recommendation: tier,
      reason: reason,
    );
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await LiquidGlassWidgets.initialize();
  runApp(LiquidGlassWidgets.wrap(
    child: const AudacityLibraryApp(),
    brightnessResolver: Theme.maybeBrightnessOf,
    theme: const GlassThemeData.ios27(),
  ));
}

class AudacityLibraryApp extends StatefulWidget {
  const AudacityLibraryApp({super.key});

  @override
  State<AudacityLibraryApp> createState() => _AudacityLibraryAppState();
}

class _AudacityLibraryAppState extends State<AudacityLibraryApp> {
  bool _loading = true;
  bool _showSetup = false;
  GlassTier _tier = GlassTier.standard;
  DeviceAssessment? _assessment;

  @override
  void initState() {
    super.initState();
    _initialize();
  }

  Future<void> _initialize() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_qualityKey);
    if (saved == null) {
      _assessment = await DeviceAssessment.run();
      _tier = _assessment!.recommendation;
      _showSetup = true;
    } else {
      _tier = GlassTier.values.firstWhere(
        (item) => item.name == saved,
        orElse: () => GlassTier.standard,
      );
    }
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _saveTier(GlassTier tier) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_qualityKey, tier.name);
    if (!mounted) return;
    setState(() {
      _tier = tier;
      _showSetup = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const CupertinoApp(
        debugShowCheckedModeBanner: false,
        home: CupertinoPageScaffold(
          child: Center(child: CupertinoActivityIndicator(radius: 16)),
        ),
      );
    }
    return CupertinoApp(
      debugShowCheckedModeBanner: false,
      theme: const CupertinoThemeData(brightness: Brightness.light),
      home: _showSetup
          ? QualitySetupScreen(
              assessment: _assessment!,
              selected: _tier,
              onSelected: (tier) => setState(() => _tier = tier),
              onContinue: () => _saveTier(_tier),
            )
          : LibraryHome(
              tier: _tier,
              onTierChanged: _saveTier,
            ),
    );
  }
}

class QualitySetupScreen extends StatelessWidget {
  const QualitySetupScreen({
    required this.assessment,
    required this.selected,
    required this.onSelected,
    required this.onContinue,
    super.key,
  });

  final DeviceAssessment assessment;
  final GlassTier selected;
  final ValueChanged<GlassTier> onSelected;
  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    return GlassScaffold(
      appBar: const GlassAppBar(title: Text('Preparando tu biblioteca')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 120),
          children: [
            const Icon(CupertinoIcons.sparkles, size: 42),
            const SizedBox(height: 16),
            const Text('Calidad Liquid Glass',
                style: TextStyle(fontSize: 29, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text('Analizamos las características del dispositivo para recomendar la mejor experiencia disponible.'),
            const SizedBox(height: 18),
            _InfoPanel(assessment: assessment),
            const SizedBox(height: 20),
            for (final tier in GlassTier.values)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _TierOption(
                  tier: tier,
                  selected: selected == tier,
                  recommended: tier == assessment.recommendation,
                  onTap: () => onSelected(tier),
                ),
              ),
            const SizedBox(height: 16),
            CupertinoButton.filled(
              onPressed: onContinue,
              child: const Text('Continuar'),
            ),
            const SizedBox(height: 8),
            const Text(
              'Esta elección se preguntará una sola vez. Podrás cambiarla después en Ajustes.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: CupertinoColors.secondaryLabel),
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoPanel extends StatelessWidget {
  const _InfoPanel({required this.assessment});
  final DeviceAssessment assessment;

  @override
  Widget build(BuildContext context) => GlassContainer.card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(assessment.model,
                style: const TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text('RAM: ${assessment.ramGb > 0 ? '${assessment.ramGb} GB' : 'No disponible'}  ·  CPU: ${assessment.cores > 0 ? assessment.cores : 'N/D'} núcleos'),
            const SizedBox(height: 8),
            Text(assessment.reason,
                style: const TextStyle(fontSize: 13, color: CupertinoColors.secondaryLabel)),
          ]),
        ),
      );
}

class _TierOption extends StatelessWidget {
  const _TierOption({
    required this.tier,
    required this.selected,
    required this.recommended,
    required this.onTap,
  });

  final GlassTier tier;
  final bool selected;
  final bool recommended;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => GestureDetector(
        onTap: onTap,
        child: GlassContainer.card(
          child: Padding(
            padding: const EdgeInsets.all(15),
            child: Row(children: [
              Icon(
                selected ? CupertinoIcons.check_mark_circled_solid : CupertinoIcons.circle,
                color: selected ? CupertinoColors.activeBlue : CupertinoColors.secondaryLabel,
                size: 23,
              ),
              const SizedBox(width: 12),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Text(tier.label, style: const TextStyle(fontWeight: FontWeight.w700)),
                  if (recommended) ...[
                    const SizedBox(width: 8),
                    const Text('RECOMENDADA', style: TextStyle(fontSize: 9, color: CupertinoColors.activeBlue, fontWeight: FontWeight.bold)),
                  ],
                ]),
                const SizedBox(height: 4),
                Text(tier.description, style: const TextStyle(fontSize: 12, color: CupertinoColors.secondaryLabel)),
              ])),
            ]),
          ),
        ),
      );
}

class LibraryHome extends StatefulWidget {
  const LibraryHome({required this.tier, required this.onTierChanged, super.key});
  final GlassTier tier;
  final ValueChanged<GlassTier> onTierChanged;

  @override
  State<LibraryHome> createState() => _LibraryHomeState();
}

class _LibraryHomeState extends State<LibraryHome> {
  int _tab = 0;
  String _status = 'Audacity original listo para abrir desde el motor Andacious.';

  Future<void> _openAudacity() async {
    try {
      await _runtime.invokeMethod<void>('openAudacity');
      setState(() => _status = 'Solicitud enviada al entorno Andacious.');
    } on PlatformException {
      setState(() => _status = 'El puente Android–Andacious aún debe integrarse en el host.');
    } on MissingPluginException {
      setState(() => _status = 'Interfaz Flutter en preparación: falta conectar el host Andacious.');
    }
  }

  @override
  Widget build(BuildContext context) {
    final titles = ['Biblioteca', 'Recientes', 'Ajustes'];
    return GlassScaffold(
      appBar: GlassAppBar(title: Text(titles[_tab])),
      bottomBar: GlassTabBar.bottom(
        selectedIndex: _tab,
        onTabSelected: (index) => setState(() => _tab = index),
        tabs: const [
          GlassTab(icon: Icon(CupertinoIcons.music_note_list), label: 'Biblioteca'),
          GlassTab(icon: Icon(CupertinoIcons.clock), label: 'Recientes'),
          GlassTab(icon: Icon(CupertinoIcons.gear), label: 'Ajustes'),
        ],
      ),
      body: SafeArea(
        child: IndexedStack(
          index: _tab,
          children: [
            _libraryTab(),
            _recentTab(),
            _settingsTab(),
          ],
        ),
      ),
    );
  }

  Widget _libraryTab() => ListView(
        padding: const EdgeInsets.fromLTRB(18, 18, 18, 120),
        children: [
          const Text('Tu audio, en un solo lugar',
              style: TextStyle(fontSize: 27, fontWeight: FontWeight.w700)),
          const SizedBox(height: 7),
          const Text('Biblioteca local · Audacity 4.0.2',
              style: TextStyle(color: CupertinoColors.secondaryLabel)),
          const SizedBox(height: 22),
          GlassContainer.card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Icon(CupertinoIcons.waveform, size: 32),
                const SizedBox(height: 12),
                const Text('Abrir Audacity 4.0.2',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
                const SizedBox(height: 6),
                const Text('Se abrirá el programa original dentro del escritorio Linux de Andacious.'),
                const SizedBox(height: 16),
                CupertinoButton.filled(
                  onPressed: _openAudacity,
                  child: const Text('Iniciar Audacity'),
                ),
              ]),
            ),
          ),
          const SizedBox(height: 18),
          Text(_status, style: const TextStyle(fontSize: 12, color: CupertinoColors.secondaryLabel)),
          const SizedBox(height: 24),
          const Text('Biblioteca local',
              style: TextStyle(fontSize: 19, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          const Text('La lectura de archivos y el selector de audio se conectarán al almacenamiento Android en la siguiente integración. Audacity seguirá abriendo y editando los archivos con su interfaz original.',
              style: TextStyle(color: CupertinoColors.secondaryLabel)),
        ],
      );

  Widget _recentTab() => const Center(
        child: Text('Los proyectos recientes aparecerán aquí cuando se conecte el historial del runtime.'),
      );

  Widget _settingsTab() => ListView(
        padding: const EdgeInsets.all(18),
        children: [
          const Text('Liquid Glass',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          Text('Calidad actual: ${widget.tier.label}'),
          const SizedBox(height: 14),
          for (final tier in GlassTier.values)
            CupertinoListTile(
              title: Text(tier.label),
              subtitle: Text(tier.description),
              trailing: widget.tier == tier
                  ? const Icon(CupertinoIcons.check_mark_circled_solid, color: CupertinoColors.activeBlue)
                  : null,
              onTap: () => widget.onTierChanged(tier),
            ),
          const SizedBox(height: 20),
          const Text('Estos ajustes solo afectan a la biblioteca Flutter. No modifican la interfaz, herramientas ni ventanas del Audacity original.',
              style: TextStyle(fontSize: 12, color: CupertinoColors.secondaryLabel)),
        ],
      );
}

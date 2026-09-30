import 'dart:async';
import 'package:flutter/material.dart';
import 'package:percent_indicator/percent_indicator.dart';
import '../services/connection_service.dart';
import '../services/phone_health_service.dart';

class HealthMonitorScreen extends StatefulWidget {
  const HealthMonitorScreen({super.key});

  @override
  State<HealthMonitorScreen> createState() => _HealthMonitorScreenState();
}

class _HealthMonitorScreenState extends State<HealthMonitorScreen> {
  final _conn = ConnectionService();
  final _phoneHealthService = PhoneHealthService();
  StreamSubscription<bool>? _statusSub;
  bool _connected = false;
  bool _loading = false;

  Map<String, dynamic>? _pcHealth;
  Map<String, dynamic>? _pcAnalysis;
  Map<String, dynamic>? _phoneHealth;
  Map<String, dynamic>? _phoneAnalysis;

  @override
  void initState() {
    super.initState();
    _connected = _conn.connected;
    _statusSub = _conn.connectionStatus.listen((isConnected) {
      if (mounted) setState(() => _connected = isConnected);
    });
    _fetchAll();
  }

  @override
  void dispose() {
    _statusSub?.cancel();
    super.dispose();
  }

  Future<void> _fetchAll() async {
    setState(() => _loading = true);
    if (_connected) {
      final response = await _conn.sendAndWait({'type': 'get_health'});
      if (response['data'] != null) {
        _pcHealth = Map<String, dynamic>.from(response['data']);
        _pcAnalysis = response['analysis'] != null ? Map<String, dynamic>.from(response['analysis']) : null;
      }
    }
    final phoneData = await _phoneHealthService.getPhoneHealth();
    _phoneHealth = phoneData;
    _phoneAnalysis = _phoneHealthService.analyzePhoneHealth(phoneData);
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        elevation: 0,
        title: const Text('Health Monitor', style: TextStyle(color: Colors.white)),
        iconTheme: const IconThemeData(color: Colors.white),
        actions: [
          IconButton(icon: const Icon(Icons.refresh, color: Colors.white), onPressed: _fetchAll),
        ],
      ),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator(color: Color(0xFF6C5CE7)))
            : RefreshIndicator(
                onRefresh: _fetchAll,
                color: const Color(0xFF6C5CE7),
                backgroundColor: const Color(0xFF111120),
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _card('PC Health', _pcHealth, _buildPcBody(), _pcAnalysis),
                    const SizedBox(height: 14),
                    _card('Phone Health', _phoneHealth, _buildPhoneBody(), _phoneAnalysis),
                  ],
                ),
              ),
      ),
    );
  }

  Widget _card(String title, Map<String, dynamic>? data, Widget body, Map<String, dynamic>? analysis) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF111120),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1E1E32)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w700)),
          const Divider(color: Color(0xFF1E1E32), height: 20),
          if (data == null)
            const Text('Not connected or no data yet', style: TextStyle(color: Color(0xFF8888aa), fontSize: 12))
          else if (data.containsKey('error'))
            Text('${data['error']}', style: const TextStyle(color: Color(0xFFEF4444), fontSize: 12))
          else
            body,
          if (analysis != null) ...[
            const Divider(color: Color(0xFF1E1E32), height: 20),
            _analysisSection(analysis),
          ],
        ],
      ),
    );
  }

  Widget _buildPcBody() {
    if (_pcHealth == null) return const SizedBox();
    return Column(
      children: [
        _metric('CPU', (_pcHealth!['cpu']['usage_percent'] as num) / 100, '${_pcHealth!['cpu']['usage_percent']}%',
            _severity(_pcHealth!['cpu']['usage_percent'], 60, 80)),
        const SizedBox(height: 10),
        _metric('RAM', (_pcHealth!['ram']['percent'] as num) / 100,
            '${_pcHealth!['ram']['used_gb']}/${_pcHealth!['ram']['total_gb']} GB', _severity(_pcHealth!['ram']['percent'], 70, 85)),
        const SizedBox(height: 10),
        _metric('Disk', (_pcHealth!['disk']['percent'] as num) / 100, '${_pcHealth!['disk']['percent']}%',
            _severity(_pcHealth!['disk']['percent'], 70, 85)),
        if (_pcHealth!['battery'] != null) ...[
          const SizedBox(height: 10),
          _metric(
            'Battery',
            (_pcHealth!['battery']['percent'] as num) / 100,
            '${_pcHealth!['battery']['percent']}%${_pcHealth!['battery']['plugged_in'] == true ? ' ⚡' : ''}',
            _severity(100 - (_pcHealth!['battery']['percent'] as num), 60, 80),
          ),
        ],
      ],
    );
  }

  Widget _buildPhoneBody() {
    if (_phoneHealth == null) return const SizedBox();
    return _metric(
      'Battery',
      (_phoneHealth!['battery']['percent'] as num) / 100,
      '${_phoneHealth!['battery']['percent']}%${_phoneHealth!['battery']['is_charging'] == true ? ' ⚡' : ''}',
      _severity(100 - (_phoneHealth!['battery']['percent'] as num), 60, 80),
    );
  }

  Color _severity(num value, num warnAt, num criticalAt) {
    if (value > criticalAt) return const Color(0xFFEF4444);
    if (value > warnAt) return const Color(0xFFF59E0B);
    return const Color(0xFF22C55E);
  }

  Widget _metric(String label, double percent, String value, Color color) {
    return Row(
      children: [
        SizedBox(width: 60, child: Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w600))),
        Expanded(
          child: LinearPercentIndicator(
            lineHeight: 7,
            percent: percent.clamp(0.0, 1.0),
            progressColor: color,
            backgroundColor: const Color(0xFF1E1E32),
            barRadius: const Radius.circular(4),
            padding: EdgeInsets.zero,
          ),
        ),
        const SizedBox(width: 8),
        SizedBox(
          width: 88,
          child: Text(value, textAlign: TextAlign.right, style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w600)),
        ),
      ],
    );
  }

  Widget _analysisSection(Map<String, dynamic> analysis) {
    final primary = (analysis['risks'] ?? analysis['issues'] ?? []) as List;
    final secondary = (analysis['recommendations'] ?? analysis['advice'] ?? []) as List;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ...primary.map((r) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 2),
              child: Text('• $r', style: const TextStyle(color: Colors.white70, fontSize: 12)),
            )),
        const SizedBox(height: 6),
        ...secondary.map((r) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 2),
              child: Text(r, style: const TextStyle(color: Color(0xFF8888aa), fontSize: 11)),
            )),
      ],
    );
  }
}

import 'package:flutter/material.dart';

class VMDrawerPanel extends StatelessWidget {
  final String activeTab, echoText;
  final double sensitivity;
  final ValueChanged<String> onTabChange;
  final VoidCallback onClose;
  final Function(Map<String, dynamic>) onSend;
  final ValueChanged<double> onSensitivityChange;
  final Function(List<String>) onHotkey;
  final Function(String) onKeypress;

  const VMDrawerPanel({super.key,
    required this.activeTab, required this.echoText,
    required this.sensitivity, required this.onTabChange,
    required this.onClose, required this.onSend,
    required this.onSensitivityChange, required this.onHotkey,
    required this.onKeypress});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.82,
      decoration: const BoxDecoration(
        color: Color(0xFF0A0A12),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        border: Border(top: BorderSide(color: Color(0xFF2A2A4A), width: 1.5)),
      ),
      child: Column(children: [
        // Grip
        Center(child: Container(
          margin: const EdgeInsets.only(top: 12, bottom: 8),
          width: 36, height: 4,
          decoration: BoxDecoration(color: const Color(0xFF1E1E32), borderRadius: BorderRadius.circular(2)),
        )),
        // Tabs
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(children: [
            for (final tab in ['type', 'shortcuts', 'keyboard', 'controls'])
              _Tab(label: _tabLabel(tab), active: activeTab == tab, onTap: () => onTabChange(tab)),
          ]),
        ),
        const Divider(height: 1, color: Color(0xFF1E1E32)),
        // Panel content
        Expanded(child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: _buildPanel(),
        )),
      ]),
    );
  }

  String _tabLabel(String t) {
    switch(t) { case 'type': return 'Type'; case 'shortcuts': return 'Shortcuts';
      case 'keyboard': return 'Keyboard'; case 'controls': return 'Controls'; default: return t; }
  }

  Widget _buildPanel() {
    switch (activeTab) {
      case 'type': return _TypePanel(echoText: echoText, onSend: onSend);
      case 'shortcuts': return _ShortcutsPanel(onHotkey: onHotkey, onKeypress: onKeypress);
      case 'keyboard': return _KeyboardPanel(onHotkey: onHotkey, onKeypress: onKeypress, onSend: onSend);
      case 'controls': return _ControlsPanel(sensitivity: sensitivity, onSensitivityChange: onSensitivityChange, onSend: onSend);
      default: return const SizedBox();
    }
  }
}

class _Tab extends StatelessWidget {
  final String label;
  final bool active;
  final VoidCallback onTap;
  const _Tab({required this.label, required this.active, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(right: 4, bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: active ? const Color(0xFF111120) : Colors.transparent,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(10)),
          border: active ? Border.all(color: const Color(0xFF2A2A4A)) : null,
        ),
        child: Text(label, style: TextStyle(
          fontSize: 12, fontWeight: FontWeight.w500,
          color: active ? Colors.white : Colors.white.withOpacity(0.4))),
      ),
    );
  }
}

// ── TYPE PANEL ──────────────────────────────────────────────────
class _TypePanel extends StatefulWidget {
  final String echoText;
  final Function(Map<String, dynamic>) onSend;
  const _TypePanel({required this.echoText, required this.onSend});
  @override State<_TypePanel> createState() => _TypePanelState();
}
class _TypePanelState extends State<_TypePanel> {
  final _ctrl = TextEditingController();

  void _send() {
    final text = _ctrl.text.trim();
    if (text.isEmpty) return;
    widget.onSend({'type': 'keypress', 'text': text});
    setState(() => _ctrl.clear());
  }

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      // Mirror box
      Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFF111120),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF2A2A4A), width: 1.5),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('WHAT WILL BE TYPED ON PC',
            style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.4), letterSpacing: 0.8)),
          const SizedBox(height: 8),
          Text(_ctrl.text.isEmpty ? 'Start typing below...' : _ctrl.text,
            style: TextStyle(
              fontSize: 17, fontFamily: 'monospace',
              color: _ctrl.text.isEmpty ? Colors.white.withOpacity(0.25) : Colors.white,
              height: 1.5,
            )),
        ]),
      ),
      // Echo
      if (widget.echoText.isNotEmpty) ...[
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: const Color(0xFF0A1A0A),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: const Color(0xFF00D68F).withOpacity(0.3)),
          ),
          child: Text(widget.echoText,
            style: const TextStyle(fontSize: 12, color: Color(0xFF00D68F), fontFamily: 'monospace')),
        ),
      ],
      const SizedBox(height: 10),
      // Input
      TextField(
        controller: _ctrl,
        onChanged: (_) => setState(() {}),
        style: const TextStyle(color: Colors.white, fontFamily: 'monospace', fontSize: 16),
        decoration: InputDecoration(
          hintText: 'Type here — see preview above',
          hintStyle: TextStyle(color: Colors.white.withOpacity(0.3), fontFamily: 'monospace'),
          filled: true, fillColor: const Color(0xFF0A0A12),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(14),
            borderSide: const BorderSide(color: Color(0xFF2A2A4A))),
          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14),
            borderSide: const BorderSide(color: Color(0xFF2A2A4A))),
          focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14),
            borderSide: const BorderSide(color: Color(0xFF6C5CE7))),
        ),
      ),
      const SizedBox(height: 10),
      Row(children: [
        Expanded(child: FilledButton(
          onPressed: _send,
          style: FilledButton.styleFrom(
            backgroundColor: const Color(0xFF6C5CE7),
            padding: const EdgeInsets.symmetric(vertical: 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          ),
          child: const Text('Send to PC ↵', style: TextStyle(fontWeight: FontWeight.w600)),
        )),
        const SizedBox(width: 8),
        OutlinedButton(
          onPressed: () => setState(() => _ctrl.clear()),
          style: OutlinedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
            side: const BorderSide(color: Color(0xFF2A2A4A)),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          ),
          child: Text('Clear', style: TextStyle(color: Colors.white.withOpacity(0.5))),
        ),
      ]),
    ]);
  }
}

// ── SHORTCUTS PANEL ─────────────────────────────────────────────
class _ShortcutsPanel extends StatelessWidget {
  final Function(List<String>) onHotkey;
  final Function(String) onKeypress;
  const _ShortcutsPanel({required this.onHotkey, required this.onKeypress});

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _SectionTitle('System'),
      _BtnGrid(buttons: [
        _ShortBtn('⇄', 'Alt+Tab', () => onHotkey(['alt','tab'])),
        _ShortBtn('⊞', 'Desktop', () => onHotkey(['super','d'])),
        _ShortBtn('🔒', 'Lock PC', () => onHotkey(['super','l'])),
        _ShortBtn('📸', 'Screenshot', () => onHotkey(['super','shift','s'])),
        _ShortBtn('📊', 'Task Mgr', () => onHotkey(['ctrl','shift','escape'])),
        _ShortBtn('⚙️', 'Settings', () => onHotkey(['super','i'])),
        _ShortBtn('✕', 'Close Win', () => onHotkey(['alt','f4'])),
        _ShortBtn('⎋', 'Escape', () => onKeypress('escape')),
      ]),
      const SizedBox(height: 8),
      _SectionTitle('Clipboard'),
      _BtnGrid(buttons: [
        _ShortBtn('⌘C', 'Copy', () => onHotkey(['ctrl','c']), color: const Color(0xFF00D68F)),
        _ShortBtn('⌘V', 'Paste', () => onHotkey(['ctrl','v']), color: const Color(0xFF00D68F)),
        _ShortBtn('⌘Z', 'Undo', () => onHotkey(['ctrl','z']), color: const Color(0xFF00D68F)),
        _ShortBtn('⌘Y', 'Redo', () => onHotkey(['ctrl','y']), color: const Color(0xFF00D68F)),
        _ShortBtn('⌘A', 'Select All', () => onHotkey(['ctrl','a']), color: const Color(0xFF00D68F)),
        _ShortBtn('⌘S', 'Save', () => onHotkey(['ctrl','s']), color: const Color(0xFF00D68F)),
        _ShortBtn('⌘F', 'Find', () => onHotkey(['ctrl','f']), color: const Color(0xFF00D68F)),
        _ShortBtn('⌘P', 'Print', () => onHotkey(['ctrl','p']), color: const Color(0xFF00D68F)),
      ]),
      const SizedBox(height: 8),
      _SectionTitle('Media'),
      _BtnGrid(buttons: [
        _ShortBtn('⏯', 'Play/Pause', () => onKeypress('playpause')),
        _ShortBtn('⏭', 'Next', () => onKeypress('nexttrack')),
        _ShortBtn('⏮', 'Prev', () => onKeypress('prevtrack')),
        _ShortBtn('🔇', 'Mute', () => onKeypress('volumemute')),
        _ShortBtn('🔊', 'Vol Up', () => onKeypress('volumeup')),
        _ShortBtn('🔉', 'Vol Down', () => onKeypress('volumedown')),
        _ShortBtn('↺', 'Refresh', () => onKeypress('f5')),
        _ShortBtn('⛶', 'Fullscreen', () => onKeypress('f11')),
      ]),
    ]);
  }
}

// ── KEYBOARD PANEL ──────────────────────────────────────────────
class _KeyboardPanel extends StatefulWidget {
  final Function(List<String>) onHotkey;
  final Function(String) onKeypress;
  final Function(Map<String, dynamic>) onSend;
  const _KeyboardPanel({required this.onHotkey, required this.onKeypress, required this.onSend});
  @override State<_KeyboardPanel> createState() => _KeyboardPanelState();
}
class _KeyboardPanelState extends State<_KeyboardPanel> {
  bool _shift = false;
  final _rows = [
    ['q','w','e','r','t','y','u','i','o','p'],
    ['a','s','d','f','g','h','j','k','l'],
    ['z','x','c','v','b','n','m'],
  ];

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      for (int r = 0; r < _rows.length; r++) ...[
        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          if (r == 2) _Key('⇧', wide: true, accent: _shift, onTap: () => setState(() => _shift = !_shift)),
          for (final k in _rows[r]) _Key(_shift ? k.toUpperCase() : k,
            onTap: () => widget.onKeypress(_shift ? k.toUpperCase() : k)),
          if (r == 2) _Key('⌫', wide: true, accent: true, onTap: () => widget.onKeypress('backspace')),
        ]),
        const SizedBox(height: 4),
      ],
      Row(mainAxisAlignment: MainAxisAlignment.center, children: [
        _Key('Tab', wide: true, accent: true, onTap: () => widget.onKeypress('tab')),
        _Key('space', extraWide: true, onTap: () => widget.onKeypress('space')),
        _Key('↵', wide: true, accent: true, onTap: () => widget.onKeypress('enter')),
      ]),
      const SizedBox(height: 8),
      Wrap(spacing: 4, runSpacing: 4, children: [
        _SmallBtn('⎋ Esc', () => widget.onKeypress('escape')),
        _SmallBtn('⌘ Copy', () => widget.onHotkey(['ctrl','c'])),
        _SmallBtn('⌘ Paste', () => widget.onHotkey(['ctrl','v'])),
        _SmallBtn('⌘ Undo', () => widget.onHotkey(['ctrl','z'])),
        _SmallBtn('↑', () => widget.onKeypress('up')),
        _SmallBtn('↓', () => widget.onKeypress('down')),
        _SmallBtn('←', () => widget.onKeypress('left')),
        _SmallBtn('→', () => widget.onKeypress('right')),
      ]),
    ]);
  }
}

// ── CONTROLS PANEL ──────────────────────────────────────────────
class _ControlsPanel extends StatelessWidget {
  final double sensitivity;
  final ValueChanged<double> onSensitivityChange;
  final Function(Map<String, dynamic>) onSend;
  const _ControlsPanel({required this.sensitivity, required this.onSensitivityChange, required this.onSend});

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _SectionTitle('Scroll'),
      Row(mainAxisAlignment: MainAxisAlignment.center, children: [
        _ScrollBtn('▲', () => onSend({'type':'scroll','dy':5})),
        const SizedBox(width: 20),
        Text('Scroll', style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.4))),
        const SizedBox(width: 20),
        _ScrollBtn('▼', () => onSend({'type':'scroll','dy':-5})),
      ]),
      const SizedBox(height: 16),
      _SectionTitle('Cursor Speed'),
      Row(children: [
        Text('Slow', style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.4))),
        Expanded(child: Slider(
          value: sensitivity, min: 0.5, max: 5.0,
          activeColor: const Color(0xFF6C5CE7),
          inactiveColor: const Color(0xFF1E1E32),
          onChanged: onSensitivityChange,
        )),
        Text('Fast', style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.4))),
        const SizedBox(width: 8),
        Text('${sensitivity.toStringAsFixed(1)}x',
          style: const TextStyle(fontSize: 12, color: Color(0xFF6C5CE7), fontFamily: 'monospace')),
      ]),
    ]);
  }
}

// ── Shared widgets ──────────────────────────────────────────────
class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Text(text.toUpperCase(),
      style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.4), letterSpacing: 0.8, fontWeight: FontWeight.w500)),
  );
}

class _BtnGrid extends StatelessWidget {
  final List<Widget> buttons;
  const _BtnGrid({required this.buttons});
  @override
  Widget build(BuildContext context) => GridView.count(
    crossAxisCount: 4, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(),
    mainAxisSpacing: 6, crossAxisSpacing: 6, childAspectRatio: 1.1,
    children: buttons,
  );
}

class _ShortBtn extends StatelessWidget {
  final String icon, label;
  final VoidCallback onTap;
  final Color? color;
  const _ShortBtn(this.icon, this.label, this.onTap, {this.color});
  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    child: Container(
      decoration: BoxDecoration(
        color: const Color(0xFF111120),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFF1E1E32)),
      ),
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Text(icon, style: TextStyle(fontSize: 16, color: color ?? const Color(0xFF6C5CE7))),
        const SizedBox(height: 4),
        Text(label, textAlign: TextAlign.center,
          style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.5))),
      ]),
    ),
  );
}

class _Key extends StatelessWidget {
  final String label;
  final bool wide, extraWide, accent;
  final VoidCallback onTap;
  const _Key(this.label, {this.wide=false, this.extraWide=false, this.accent=false, required this.onTap});
  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    child: Container(
      width: extraWide ? 120 : wide ? 52 : 32,
      height: 40, margin: const EdgeInsets.all(2),
      decoration: BoxDecoration(
        color: accent ? const Color(0xFF1E1E32) : const Color(0xFF181828),
        borderRadius: BorderRadius.circular(7),
        border: Border.all(color: const Color(0xFF1E1E32)),
      ),
      child: Center(child: Text(label,
        style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500,
          color: accent ? Colors.white.withOpacity(0.6) : Colors.white))),
    ),
  );
}

class _SmallBtn extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _SmallBtn(this.label, this.onTap);
  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    child: Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
      decoration: BoxDecoration(
        color: const Color(0xFF111120), borderRadius: BorderRadius.circular(7),
        border: Border.all(color: const Color(0xFF1E1E32)),
      ),
      child: Text(label, style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.6))),
    ),
  );
}

class _ScrollBtn extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _ScrollBtn(this.label, this.onTap);
  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    child: Container(
      width: 52, height: 40,
      decoration: BoxDecoration(
        color: const Color(0xFF111120), borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFF1E1E32)),
      ),
      child: Center(child: Text(label, style: const TextStyle(fontSize: 18, color: Colors.white))),
    ),
  );
}

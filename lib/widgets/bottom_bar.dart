import 'package:flutter/material.dart';

class VMBottomBar extends StatelessWidget {
  final VoidCallback onLeftClick, onDoubleClick, onRightClick, onVoice, onDrawer;
  final String logText;

  const VMBottomBar({super.key,
    required this.onLeftClick, required this.onDoubleClick,
    required this.onRightClick, required this.onVoice,
    required this.onDrawer, required this.logText});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF0A0A12),
        border: Border(top: BorderSide(color: Color(0xFF1E1E32))),
      ),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        // Click buttons row
        IntrinsicHeight(
          child: Row(children: [
            _ClickBtn(icon: '◉', label: 'Left Click', onTap: onLeftClick),
            const VerticalDivider(width: 1, color: Color(0xFF1E1E32)),
            _ClickBtn(icon: '⊕', label: 'Double', onTap: onDoubleClick),
            const VerticalDivider(width: 1, color: Color(0xFF1E1E32)),
            _ClickBtn(icon: '◎', label: 'Right Click', onTap: onRightClick),
          ]),
        ),
        const Divider(height: 1, color: Color(0xFF1E1E32)),
        // Voice + drawer row
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: Row(children: [
            _CircleBtn(icon: Icons.mic, onTap: onVoice, active: false),
            const SizedBox(width: 12),
            Expanded(child: Text(logText,
              style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.4),
                fontStyle: FontStyle.italic),
              overflow: TextOverflow.ellipsis)),
            _CircleBtn(icon: Icons.keyboard_arrow_up, onTap: onDrawer, active: false),
          ]),
        ),
      ]),
    );
  }
}

class _ClickBtn extends StatelessWidget {
  final String icon, label;
  final VoidCallback onTap;
  const _ClickBtn({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Expanded(child: InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(icon, style: const TextStyle(fontSize: 18, color: Color(0xFF6C5CE7))),
          const SizedBox(height: 3),
          Text(label, style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.5))),
        ]),
      ),
    ));
  }
}

class _CircleBtn extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final bool active;
  const _CircleBtn({required this.icon, required this.onTap, required this.active});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 44, height: 44,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: active ? const Color(0xFFFF5C6A) : const Color(0xFF111120),
          border: Border.all(color: const Color(0xFF1E1E32), width: 1.5),
        ),
        child: Icon(icon, size: 20,
          color: active ? Colors.white : Colors.white.withOpacity(0.5)),
      ),
    );
  }
}

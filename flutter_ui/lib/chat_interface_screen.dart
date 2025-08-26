import 'package:flutter/material.dart';
import 'dart:ui';
import 'package:flutter/services.dart';

// --- Helper Classes (Add these at the bottom of the file) ---

enum ChatUser { user, ai }
enum AiModel { fast, smart }

class ChatMessage {
  final String text;
  final ChatUser user;
  ChatMessage({required this.text, required this.user});
}

// --- Main Screen Widget ---

class ChatInterfaceScreen extends StatefulWidget {
  const ChatInterfaceScreen({super.key});

  @override
  State<ChatInterfaceScreen> createState() => _ChatInterfaceScreenState();
}

class _ChatInterfaceScreenState extends State<ChatInterfaceScreen>
    with TickerProviderStateMixin {
  final TextEditingController _textController = TextEditingController();
  final List<ChatMessage> _messages = [];
  final FocusNode _textFieldFocusNode = FocusNode();
  bool _isChatting = false;
  AiModel _selectedModel = AiModel.fast;
  bool _isModelSelectorOpen = false;
  bool _isMenuOpen = false;
  late AnimationController _sendButtonAnimationController;

  @override
  void initState() {
    super.initState();
    _textFieldFocusNode.addListener(_onFocusChange);
    _textController.addListener(_onTextChanged);
    _sendButtonAnimationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 200),
    );
  }

  void _onFocusChange() {
    if (_textFieldFocusNode.hasFocus && !_isChatting) {
      setState(() => _isChatting = true);
    }
  }

  void _onTextChanged() {
    if (_textController.text.isNotEmpty) {
      _sendButtonAnimationController.forward();
    } else {
      _sendButtonAnimationController.reverse();
    }
  }

  @override
  void dispose() {
    _textController.removeListener(_onTextChanged);
    _textFieldFocusNode.removeListener(_onFocusChange);
    _textController.dispose();
    _textFieldFocusNode.dispose();
    _sendButtonAnimationController.dispose();
    super.dispose();
  }

  void _handleSendPressed() {
    final text = _textController.text;
    if (text.isEmpty) return;

    _textController.clear();
    FocusScope.of(context).unfocus();
    HapticFeedback.mediumImpact();

    setState(() {
      _messages.add(ChatMessage(text: text, user: ChatUser.user));
      if (!_isChatting) _isChatting = true;
    });

    Future.delayed(const Duration(milliseconds: 500), () {
      setState(() {
        final modelResponse = _selectedModel == AiModel.fast
            ? "Response from Y-Fast."
            : "A more detailed and thoughtful response from Y-Smart.";
        _messages.add(ChatMessage(text: modelResponse, user: ChatUser.ai));
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFDBDBDB),
      body: Center(
        child: SizedBox(
          width: 393,
          height: 852,
          child: Stack(
            children: [
              // --- Main Chat UI (Stays in place) ---
              Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 40, 20, 10),
                    child: Row(
                      children: [
                        _PolishedHamburgerMenu(onTap: () {
                          setState(() => _isMenuOpen = true);
                        }),
                      ],
                    ),
                  ),
                  Expanded(
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        AnimatedOpacity(
                          opacity: _isChatting ? 0.0 : 1.0,
                          duration: const Duration(milliseconds: 500),
                          child: Image.asset(
                            'assets/images/y_black.png',
                            width: 311.815,
                            height: 485.176,
                            fit: BoxFit.contain,
                          ),
                        ),
                        if (_isChatting)
                          AnimatedOpacity(
                            opacity: _isChatting ? 1.0 : 0.0,
                            duration: const Duration(milliseconds: 500),
                            child: _buildChatListView(),
                          ),
                      ],
                    ),
                  ),
                  _buildInputSection(),
                ],
              ),
              
              // --- Side Menu Overlay (Slides on top) ---
              _buildMenuOverlay(),
              
              // --- Model Selector Pop-up ---
              _buildModelSelectorPopup(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMenuOverlay() {
    return IgnorePointer(
      ignoring: !_isMenuOpen,
      child: AnimatedOpacity(
        opacity: _isMenuOpen ? 1.0 : 0.0,
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeOut,
        child: GestureDetector(
          onTap: () => setState(() => _isMenuOpen = false), // Tap background to close
          child: Container(
            color: Colors.black.withOpacity(0.01), // Catches taps without being visible
            child: AnimatedSlide(
              duration: const Duration(milliseconds: 400),
              curve: Curves.easeInOutCubic,
              offset: _isMenuOpen ? Offset.zero : const Offset(-1.0, 0),
              child: _MenuScreen(onClose: () => setState(() => _isMenuOpen = false)),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildChatListView() {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      reverse: true,
      itemCount: _messages.length,
      itemBuilder: (context, index) {
        final message = _messages.reversed.toList()[index];
        return _ChatMessageWidget(message: message);
      },
    );
  }

  Widget _buildInputSection() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 36),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: Container(
            height: 65,
            padding: const EdgeInsets.symmetric(horizontal: 10),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.65),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.white.withOpacity(0.4)),
            ),
            child: Row(
              children: [
                GestureDetector(
                  onTap: () {
                    HapticFeedback.lightImpact();
                    setState(() => _isModelSelectorOpen = !_isModelSelectorOpen);
                  },
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: _isModelSelectorOpen
                          ? Colors.black.withOpacity(0.1)
                          : const Color.fromRGBO(211, 208, 208, 0.6),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        Image.asset('assets/images/green_dot_icon.png', width: 24, height: 24),
                        const SizedBox(width: 8),
                        const Text(
                          "Model",
                          style: TextStyle(
                              color: Color.fromRGBO(64, 62, 62, 0.9),
                              fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: TextField(
                    controller: _textController,
                    focusNode: _textFieldFocusNode,
                    style: const TextStyle(color: Colors.black87),
                    cursorColor: Colors.grey.shade700,
                    decoration: const InputDecoration(
                      hintText: 'Message Y...',
                      hintStyle: TextStyle(color: Colors.black45),
                      border: InputBorder.none,
                    ),
                  ),
                ),
                ScaleTransition(
                  scale: Tween<double>(begin: 0.0, end: 1.0).animate(CurvedAnimation(
                    parent: _sendButtonAnimationController,
                    curve: Curves.easeOutBack,
                  )),
                  child: Container(
                    decoration: const BoxDecoration(
                        color: Colors.black, shape: BoxShape.circle),
                    child: IconButton(
                      icon: const Icon(Icons.arrow_upward_rounded, color: Colors.white),
                      onPressed: _handleSendPressed,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildModelSelectorPopup() {
    return Positioned(
      bottom: 110,
      left: 20,
      child: IgnorePointer(
        ignoring: !_isModelSelectorOpen,
        child: AnimatedSlide(
          duration: const Duration(milliseconds: 500),
          curve: Curves.elasticOut,
          offset: _isModelSelectorOpen ? Offset.zero : const Offset(0, 0.5),
          child: AnimatedOpacity(
            duration: const Duration(milliseconds: 300),
            opacity: _isModelSelectorOpen ? 1.0 : 0.0,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.25),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.white.withOpacity(0.2)),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _ModelSelectorButton(
                        icon: Icons.bolt,
                        label: 'Y-Fast',
                        isSelected: _selectedModel == AiModel.fast,
                        onTap: () => setState(() {
                          _selectedModel = AiModel.fast;
                          _isModelSelectorOpen = false;
                        }),
                      ),
                      const SizedBox(height: 8),
                      _ModelSelectorButton(
                        icon: Icons.psychology_outlined,
                        label: 'Y-Smart',
                        isSelected: _selectedModel == AiModel.smart,
                        onTap: () => setState(() {
                          _selectedModel = AiModel.smart;
                          _isModelSelectorOpen = false;
                        }),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// --- Custom Widgets ---

class _PolishedHamburgerMenu extends StatelessWidget {
  final VoidCallback onTap;
  const _PolishedHamburgerMenu({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: () {
          HapticFeedback.lightImpact();
          onTap();
        },
        child: Container(
          padding: const EdgeInsets.all(8),
          child: CustomPaint(
            size: const Size(24, 16),
            painter: _HamburgerMenuPainter(),
          ),
        ),
      ),
    );
  }
}

class _ModelSelectorButton extends StatefulWidget {
  final IconData icon;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _ModelSelectorButton(
      {required this.icon,
      required this.label,
      required this.isSelected,
      required this.onTap});

  @override
  State<_ModelSelectorButton> createState() => _ModelSelectorButtonState();
}

class _ModelSelectorButtonState extends State<_ModelSelectorButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
        vsync: this,
        duration: const Duration(milliseconds: 100),
        reverseDuration: const Duration(milliseconds: 300));
    _scaleAnimation =
        Tween<double>(begin: 1.0, end: 0.95).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOut,
      reverseCurve: Curves.elasticOut,
    ));
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _animationController.forward(),
      onTapUp: (_) {
        _animationController.reverse();
        widget.onTap();
        HapticFeedback.lightImpact();
      },
      onTapCancel: () => _animationController.reverse(),
      child: ScaleTransition(
        scale: _scaleAnimation,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
          padding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          decoration: BoxDecoration(
            color: widget.isSelected
                ? Colors.white
                : Colors.black.withOpacity(0.2),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            children: [
              Icon(widget.icon,
                  size: 20,
                  color: widget.isSelected ? Colors.black : Colors.white),
              const SizedBox(width: 8),
              Text(
                widget.label,
                style: TextStyle(
                  color: widget.isSelected ? Colors.black : Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ChatMessageWidget extends StatelessWidget {
  final ChatMessage message;
  const _ChatMessageWidget({required this.message});

  @override
  Widget build(BuildContext context) {
    bool isUser = message.user == ChatUser.user;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints:
            BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        margin: const EdgeInsets.symmetric(vertical: 5),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
        decoration: BoxDecoration(
          color: isUser ? Colors.black : const Color(0xFFF0F0F0),
          gradient: isUser
              ? const LinearGradient(
                  colors: [Color(0xFF333333), Colors.black],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter)
              : null,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(20),
            topRight: const Radius.circular(20),
            bottomLeft:
                isUser ? const Radius.circular(20) : const Radius.circular(5),
            bottomRight:
                isUser ? const Radius.circular(5) : const Radius.circular(20),
          ),
        ),
        child: Text(
          message.text,
          style: TextStyle(
            color: isUser ? Colors.white : Colors.black87,
            fontSize: 16,
          ),
        ),
      ),
    );
  }
}

class _HamburgerMenuPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF91B871)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(Offset(0, 0), Offset(size.width, 0), paint);
    canvas.drawLine(
        Offset(0, size.height / 2), Offset(size.width, size.height / 2), paint);
    canvas.drawLine(
        Offset(0, size.height), Offset(size.width, size.height), paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

// --- Menu Screen Widget (Now built inside the chat screen) ---

class _MenuScreen extends StatelessWidget {
  final VoidCallback onClose;
  const _MenuScreen({required this.onClose});

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: const BorderRadius.only(
        topRight: Radius.circular(28),
        bottomRight: Radius.circular(28),
      ),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: Container(
          width: 385,
          decoration: BoxDecoration(
            color: const Color.fromRGBO(31, 30, 29, 0.20),
            borderRadius: const BorderRadius.only(
              topRight: Radius.circular(28),
              bottomRight: Radius.circular(28),
            ),
          ),
          child: SafeArea(
            child: Stack(
              children: [
                // Darker content area
                Positioned(
                  left: 23,
                  top: 120,
                  child: Container(
                    width: 345,
                    height: 331,
                    decoration: BoxDecoration(
                      color: const Color.fromRGBO(21, 17, 17, 0.84),
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
                
                // Close Button
                Positioned(
                  top: 28,
                  right: 20,
                  child: IconButton(
                    icon: const Icon(Icons.close, color: Colors.white, size: 28),
                    onPressed: () {
                      HapticFeedback.lightImpact();
                      onClose();
                    },
                  ),
                ),

                // Absolute positioned menu items
                const _MenuItem(left: 44, top: 162, icon: Icons.article_outlined, text: 'The Resume Strategist'),
                const _MenuItem(left: 40, top: 203, icon: Icons.shield_outlined, text: 'The Chamber of Trials'),
                const _MenuItem(left: 42, top: 240, icon: Icons.battery_charging_full_rounded, text: 'The Last-Minute Gambit', iconColor: Color(0xFF15B720)),
                const _MenuItem(left: 44, top: 275, icon: Icons.radar, text: 'The Radar (incl. live feed)'),
                const _MenuItem(left: 44, top: 314, icon: Icons.playlist_add_check_rounded, text: 'Get it Done List'),
                const _MenuItem(left: 44, top: 352, icon: Icons.book_outlined, text: 'Library of scholars'),
                const _MenuItem(left: 43, top: 391, icon: Icons.circle_outlined, text: 'The Inner Circle'),

                const Positioned(
                  left: 41,
                  top: 483,
                  child: Text(
                    "Chats...",
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 16.24,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _MenuItem extends StatelessWidget {
  final double left, top;
  final IconData icon;
  final String text;
  final Color iconColor;

  const _MenuItem({
    required this.left,
    required this.top,
    required this.icon,
    required this.text,
    this.iconColor = Colors.white,
  });

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: left,
      top: top,
      child: Row(
        children: [
          Icon(icon, color: iconColor, size: 24),
          const SizedBox(width: 12),
          Text(
            text,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16.24,
              fontFamily: 'SF Pro Display',
            ),
          ),
        ],
      ),
    );
  }
}
// flutter_ui/lib/chat_interface_screen.dart

import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:provider/provider.dart';
import 'services/chat_service.dart';
import 'services/theme_service.dart';

class ChatInterfaceScreen extends StatefulWidget {
  const ChatInterfaceScreen({super.key});

  @override
  State<ChatInterfaceScreen> createState() => _ChatInterfaceScreenState();
}

class _ChatInterfaceScreenState extends State<ChatInterfaceScreen> {
  final TextEditingController _textController = TextEditingController();
  double _yImageOpacity = 1.0;

  void _sendMessage() {
    if (_textController.text.isNotEmpty) {
      final userMessage = _textController.text;
      if (_yImageOpacity == 1.0) {
        setState(() {
          _yImageOpacity = 0.15; // Fade out the background
        });
      }
      _textController.clear();
      FocusScope.of(context).unfocus();
      
      // Send message through the service
      context.read<ChatService>().sendMessage(userMessage);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      body: SafeArea(
        child: Stack(
          children: [
            Center(
              child: AnimatedOpacity(
                opacity: _yImageOpacity,
                duration: const Duration(milliseconds: 500),
                curve: Curves.easeInOut,
                child: SvgPicture.asset(
                  'assets/images/chat_y_background.svg',
                  width: 312,
                  height: 486,
                  fit: BoxFit.contain,
                ),
              ),
            ),
            Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Connection status indicator
                    Consumer<ChatService>(
                      builder: (context, chatService, child) {
                        return Container(
                          margin: const EdgeInsets.only(top: 38.0, left: 26.0),
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: chatService.isConnected 
                                ? Colors.green.withOpacity(isDark ? 0.2 : 0.12)
                                : Colors.red.withOpacity(isDark ? 0.2 : 0.12),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                              color: chatService.isConnected 
                                  ? Colors.green.withOpacity(isDark ? 0.5 : 0.35)
                                  : Colors.red.withOpacity(isDark ? 0.5 : 0.35),
                              width: 1,
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Container(
                                width: 8,
                                height: 8,
                                decoration: BoxDecoration(
                                  color: chatService.isConnected 
                                      ? Colors.green 
                                      : Colors.red,
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 6),
                              Text(
                              chatService.isConnected ? 'Connected' : 'Disconnected',
                              style: TextStyle(
                                color: chatService.isConnected 
                                    ? (isDark ? Colors.green : Colors.green.shade700)
                                    : (isDark ? Colors.red : Colors.red.shade700),
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            if (!chatService.isConnected) ...[
                              const SizedBox(width: 8),
                              GestureDetector(
                                onTap: () => chatService.reconnect(),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: (isDark ? Colors.blue.withOpacity(0.2) : Colors.blue.withOpacity(0.12)),
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(
                                      color: (isDark ? Colors.blue.withOpacity(0.5) : Colors.blue.withOpacity(0.35)),
                                      width: 1,
                                    ),
                                  ),
                                  child: Text(
                                    'Reconnect',
                                    style: TextStyle(
                                      color: isDark ? Colors.blue : Colors.blue.shade700,
                                      fontSize: 10,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ),
                              ),
                            ],
                            ],
                          ),
                        );
                      },
                    ),
                    Row(
                      children: [
                        Padding(
                          padding: const EdgeInsets.only(top: 38.0, right: 8.0),
                          child: IconButton(
                            tooltip: isDark ? 'Switch to light theme' : 'Switch to dark theme',
                            icon: Icon(isDark ? Icons.light_mode : Icons.dark_mode, color: theme.colorScheme.primary),
                            onPressed: () => context.read<ThemeService>().toggleThemeMode(),
                          ),
                        ),
                        const Padding(
                          padding: EdgeInsets.only(top: 38.0, right: 26.0),
                          child: _ModelSelectionCard(),
                        ),
                      ],
                    ),
                  ],
                ),
                Expanded(child: _buildChatMessages()),
                _ChatInputBar(
                  textController: _textController,
                  onSendMessage: _sendMessage,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChatMessages() {
    return Consumer<ChatService>(
      builder: (context, chatService, child) {
        final theme = Theme.of(context);
        final isDark = theme.brightness == Brightness.dark;
        return ListView.builder(
          padding: const EdgeInsets.all(16.0),
          reverse: true,
          itemCount: chatService.messages.length,
          itemBuilder: (context, index) {
            final message = chatService.messages[index];
            final isUserMessage = message.sender == 'user';
            final isError = message.type == MessageType.error;
            final isLoading = message.type == MessageType.loading;
            
            return Align(
              alignment:
                  isUserMessage ? Alignment.centerRight : Alignment.centerLeft,
              child: Container(
                constraints: BoxConstraints(
                  maxWidth: MediaQuery.of(context).size.width * 0.7,
                ),
                margin: const EdgeInsets.symmetric(vertical: 5.0),
                padding:
                    const EdgeInsets.symmetric(horizontal: 14.0, vertical: 10.0),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12.47),
                  color: isLoading
                      ? Colors.transparent
                      : isUserMessage
                      ? (isDark ? const Color(0xFF433F3F) : const Color(0xFFE6F0FF))
                      : isError 
                          ? (isDark ? Colors.red.withOpacity(0.2) : Colors.red.withOpacity(0.12))
                          : (isDark ? const Color(0xFF2A2A2A) : Colors.white),
                ),
                child: isLoading
                    ? EphemeralThinking(exiting: context.read<ChatService>().thinkingExiting)
                    : _FadeInOnBuild(
                        child: MarkdownBody(
                          data: message.text,
                          selectable: false,
                          softLineBreak: true,
                          styleSheet: MarkdownStyleSheet(
                            p: TextStyle(
                              color: isDark ? Colors.white.withOpacity(0.90) : Colors.black87,
                              fontSize: 16,
                              height: 1.35,
                              fontWeight: FontWeight.w400,
                            ),
                            h1: TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.w700,
                              color: isDark ? const Color(0xFFEFEFEF) : Colors.black,
                            ),
                            h2: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w600,
                              color: isDark ? const Color(0xFFEFEFEF) : Colors.black87,
                            ),
                            h3: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                              color: isDark ? const Color(0xFFEFEFEF) : Colors.black87,
                            ),
                            strong: TextStyle(
                              fontWeight: FontWeight.w600,
                              color: isDark ? const Color(0xFFF5F5F5) : Colors.black,
                            ),
                            em: TextStyle(
                              fontStyle: FontStyle.italic,
                              color: isDark ? Colors.white.withOpacity(0.9) : Colors.black.withOpacity(0.75),
                            ),
                            blockquoteDecoration: BoxDecoration(
                              color: isDark ? const Color(0xFF333333) : const Color(0xFFF0F0F0),
                              border: Border(left: BorderSide(color: isDark ? Colors.white24 : Colors.black12, width: 3)),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            codeblockDecoration: BoxDecoration(
                              color: isDark ? const Color(0xFF1E1E1E) : const Color(0xFFF5F5F5),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: isDark ? Colors.white12 : Colors.black12),
                            ),
                            code: TextStyle(
                              fontSize: 14,
                              color: isDark ? const Color(0xFFE0E0E0) : Colors.black87,
                              fontWeight: FontWeight.w400,
                            ),
                            listBullet: TextStyle(
                              color: isDark ? Colors.white.withOpacity(0.85) : Colors.black54,
                              fontSize: 16,
                            ),
                            listBulletPadding: const EdgeInsets.only(right: 8),
                            tableHead: TextStyle(
                              fontWeight: FontWeight.w600,
                              color: isDark ? const Color(0xFFF0F0F0) : Colors.black,
                            ),
                            tableBody: TextStyle(
                              color: isDark ? Colors.white.withOpacity(0.85) : Colors.black87,
                              fontSize: 15,
                            ),
                            tableBorder: TableBorder.all(color: isDark ? Colors.white12 : Colors.black12, width: 1),
                            tableCellsPadding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
                            horizontalRuleDecoration: BoxDecoration(
                              border: Border(bottom: BorderSide(color: isDark ? Colors.white24 : Colors.black12, width: 1)),
                            ),
                          ),
                        ),
                      ),
              ),
            );
          },
        );
      },
    );
  }
}

class _FadeInOnBuild extends StatelessWidget {
  final Widget child;
  const _FadeInOnBuild({required this.child});

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.0, end: 1.0),
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeOut,
      builder: (context, value, _) => Opacity(opacity: value, child: child),
    );
  }
}

/// Ephemeral Text Feedback (Apple Tier)
class EphemeralThinking extends StatefulWidget {
  final bool exiting;
  const EphemeralThinking({super.key, this.exiting = false});

  @override
  State<EphemeralThinking> createState() => _EphemeralThinkingState();
}

class _EphemeralThinkingState extends State<EphemeralThinking>
    with TickerProviderStateMixin {
  late final AnimationController _driftController;
  late final AnimationController _shimmerController;
  late final Animation<double> _drift;
  Timer? _swapTimer;
  int _index = 0;

  final List<String> _phrases = const [
    'Analyzing your query',
    'Reviewing job descriptions',
    'Extracting cited skills',
    'Composing the answer',
  ];

  @override
  void initState() {
    super.initState();
    
    // Gentle Drift Animation - 3000ms sine wave for breathing effect
    _driftController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 3000),
    )..repeat(reverse: true);
    
    _drift = Tween<double>(begin: -2.0, end: 2.0).animate(
      CurvedAnimation(parent: _driftController, curve: Curves.easeInOutSine),
    );

    // Subtle Shimmer Animation - 2000ms diagonal glint
    _shimmerController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    );
    
    // Start shimmer after entry delay (250ms)
    Future.delayed(const Duration(milliseconds: 250), () {
      if (mounted) _shimmerController.repeat();
    });

    _scheduleSwap();
  }

  void _scheduleSwap() {
    _swapTimer?.cancel();
    final delay = Duration(milliseconds: 900 + math.Random().nextInt(600));
    _swapTimer = Timer(delay, () {
      if (!mounted) return;
      setState(() => _index = (_index + 1) % _phrases.length);
      _scheduleSwap();
    });
  }

  @override
  void dispose() {
    _driftController.dispose();
    _shimmerController.dispose();
    _swapTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 1.0, end: 0.0),
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeOut,
      builder: (context, bgOpacity, child) {
        final contentOpacity = widget.exiting ? 0.0 : 1.0;
        return AnimatedOpacity(
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
          opacity: contentOpacity,
          child: Stack(
            alignment: Alignment.centerLeft,
            children: [
              // Entry: subtle bubble background that fades out to 0
              Positioned.fill(
                child: IgnorePointer(
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: const Color(0xFF2A2A2A).withOpacity(bgOpacity * 0.9),
                      borderRadius: BorderRadius.circular(12.47),
                    ),
                  ),
                ),
              ),
              // Floating thinking text with gentle drift and shimmer
              AnimatedBuilder(
                animation: _drift,
                builder: (context, child) => Transform.translate(
                  offset: Offset(0, _drift.value),
                  child: child,
                ),
                child: _ShimmerText(
                  controller: _shimmerController,
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 300),
                    switchInCurve: Curves.easeInOut,
                    switchOutCurve: Curves.easeInOut,
                    layoutBuilder: (current, previous) => Stack(
                      alignment: Alignment.centerLeft,
                      children: [
                        ...previous,
                        if (current != null) current,
                      ],
                    ),
                    transitionBuilder: (w, a) => FadeTransition(opacity: a, child: w),
                    child: Text(
                      _phrases[_index],
                      key: ValueKey(_index),
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.86),
                        fontSize: 16,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _ShimmerText extends StatelessWidget {
  final AnimationController controller;
  final Widget child;
  const _ShimmerText({required this.controller, required this.child});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        // Very faint, light gradient for subtle glint effect - exact blueprint specs
        final gradient = LinearGradient(
          colors: [
            Colors.transparent,
            const Color(0xFFC8C8C8).withOpacity(0.1), // Exact blueprint: rgba(200, 200, 200, 0.1)
            Colors.transparent,
          ],
          stops: const [0.35, 0.50, 0.65], // Exact blueprint: 35%, 50%, 65%
          begin: const Alignment(-1.0, -1.0), // Diagonal from top-left
          end: const Alignment(1.0, 1.0),     // to bottom-right
          transform: _DiagonalSlide(controller.value),
        );

        return ShaderMask(
          blendMode: BlendMode.srcATop,
          shaderCallback: (bounds) => gradient.createShader(
            Rect.fromLTWH(0, 0, bounds.width, bounds.height),
          ),
          child: child,
        );
      },
    );
  }
}

class _ModelSelectionCard extends StatefulWidget {
  const _ModelSelectionCard();

  @override
  __ModelSelectionCardState createState() => __ModelSelectionCardState();
}

class __ModelSelectionCardState extends State<_ModelSelectionCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _heightAnimation;
  bool _isExpanded = false;
  String _selectedModel = 'model';

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _heightAnimation = Tween<double>(begin: 45.0, end: 135.0)
        .animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _toggleExpanded() {
    setState(() {
      _isExpanded = !_isExpanded;
      if (_isExpanded) {
        _controller.forward();
      } else {
        _controller.reverse();
      }
    });
  }

  void _onModelSelected(String model) {
    setState(() {
      _selectedModel = model;
    });
    _toggleExpanded();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
        animation: _heightAnimation,
        builder: (context, child) {
          return Container(
            width: 123,
            height: _heightAnimation.value,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8.0),
              gradient: const RadialGradient(
                center: Alignment.center,
                radius: 0.7,
                colors: [
                  Color.fromRGBO(91, 86, 86, 0.61),
                  Color.fromRGBO(72, 73, 71, 0.61),
                ],
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.2),
                  blurRadius: 17.4,
                ),
              ],
            ),
            child: SingleChildScrollView(
              physics: const NeverScrollableScrollPhysics(),
              child: Column(
                children: [
                  GestureDetector(
                    onTap: _toggleExpanded,
                    child: Container(
                      height: 45,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          SvgPicture.asset('assets/images/model_icon_green.svg',
                              width: 27, height: 27),
                          const SizedBox(width: 8),
                          Text(
                            _selectedModel,
                            style: const TextStyle(
                              fontFamily: 'PP NeueBit',
                              fontSize: 20,
                              color: Color.fromRGBO(255, 255, 255, 0.8),
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  _buildExpandedOptions(),
                ],
              ),
            ),
          );
        });
  }

  Widget _buildExpandedOptions() {
    return FadeTransition(
      opacity: _controller,
      child: Column(
        children: [
          const Divider(color: Colors.white24, height: 1, indent: 10, endIndent: 10),
          _AnimatedOption(
            animation: _controller,
            title: 'y-fast',
            onTap: () => _onModelSelected('y-fast'),
            delay: 0.1,
          ),
          _AnimatedOption(
            animation: _controller,
            title: 'y-smart',
            onTap: () => _onModelSelected('y-smart'),
            delay: 0.25,
          ),
        ],
      ),
    );
  }
}

class _AnimatedOption extends StatelessWidget {
  final Animation<double> animation;
  final String title;
  final VoidCallback onTap;
  final double delay;

  const _AnimatedOption({
    required this.animation,
    required this.title,
    required this.onTap,
    required this.delay,
  });

  @override
  Widget build(BuildContext context) {
    final curvedAnimation = CurvedAnimation(
      parent: animation,
      curve: Interval(delay, (delay + 0.6).clamp(0.0, 1.0),
          curve: Curves.easeOutCubic),
    );

    return SlideTransition(
      position: Tween<Offset>(begin: const Offset(0, -0.5), end: Offset.zero)
          .animate(curvedAnimation),
      child: FadeTransition(
        opacity: curvedAnimation,
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: onTap,
            child: Container(
              height: 44,
              alignment: Alignment.center,
              child: Text(
                title,
                style: const TextStyle(color: Colors.white, fontSize: 16),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ChatInputBar extends StatefulWidget {
  final TextEditingController textController;
  final VoidCallback onSendMessage;

  const _ChatInputBar({
    required this.textController,
    required this.onSendMessage,
  });

  @override
  __ChatInputBarState createState() => __ChatInputBarState();
}

class __ChatInputBarState extends State<_ChatInputBar>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _heightAnimation;
  bool _isExpanded = false;

  @override
  void initState() {
    super.initState();
    widget.textController.addListener(() {
      setState(() {});
    });
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    _heightAnimation = Tween<double>(begin: 65.0, end: 280.0)
        .animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _toggleExpand() {
    setState(() {
      _isExpanded = !_isExpanded;

      if (_isExpanded) {
        _controller.forward();
      } else {
        _controller.reverse();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final bool hasText = widget.textController.text.isNotEmpty;


    return Padding(
      padding: const EdgeInsets.fromLTRB(28.0, 16.0, 28.0, 32.0),
      child: AnimatedBuilder(
        animation: _heightAnimation,
        builder: (context, child) {
          return Container(
            height: _heightAnimation.value,
            padding: const EdgeInsets.symmetric(horizontal: 8.0),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12.47),
              color: const Color(0xFF252424),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.25),
                  blurRadius: 4,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: SingleChildScrollView(
              physics: const NeverScrollableScrollPhysics(),
              child: Column(
                children: [
                  Container(
                    height: 65,
                    child: Row(
                      children: [
                        IconButton(
                          icon: AnimatedRotation(
                            turns: _isExpanded ? 0.5 : 0,
                            duration: const Duration(milliseconds: 300),
                            child: const Icon(
                              Icons.expand_more,
                              color: Colors.white,
                            ),
                          ),
                          onPressed: _toggleExpand,
                        ),
                        Expanded(
                          child: TextField(
                            controller: widget.textController,
                            style: const TextStyle(
                              color: Colors.white70,
                              fontWeight: FontWeight.w500,
                              fontSize: 18,
                            ),
                            decoration: const InputDecoration(
                              hintText:
                                  'What are the most sought after skills ?..',
                              hintStyle: TextStyle(
                                color: Color.fromRGBO(255, 255, 255, 0.70),
                                fontSize: 18,
                                fontWeight: FontWeight.w500,
                              ),
                              border: InputBorder.none,
                            ),
                          ),
                        ),
                        IconButton(
                          icon: Icon(
                            Icons.arrow_upward,
                            color: hasText ? Colors.white : Colors.grey,
                          ),
                          onPressed: hasText ? widget.onSendMessage : null,
                        ),
                      ],
                    ),
                  ),
                  if (_isExpanded) _buildExpandedContent(),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildExpandedContent() {
    return FadeTransition(
      opacity: _controller,
      child: Column(
        children: [

          const Divider(color: Colors.white24, height: 1),
          const SizedBox(height: 15),
          _AnimatedCardRow(
            animation: _controller,
            iconName: 'assets/images/axe_icon.svg',
            text: 'The Resume Strategist',
            intervalStart: 0.1,
          ),
          _AnimatedCardRow(
            animation: _controller,
            iconName: 'assets/images/boxes_icon.svg',
            text: 'The Chamber of Trials',
            intervalStart: 0.2,
          ),
          _AnimatedCardRow(
            animation: _controller,
            iconName: 'assets/images/battery_charging_icon.svg',
            text: 'The Last-Minute Gambit',
            intervalStart: 0.3,
          ),
          _AnimatedCardRow(
            animation: _controller,
            iconName: 'assets/images/signal_icon.svg',
            text: 'The Radar (incl. live feed of policies)',
            intervalStart: 0.4,
          ),
        ],
      ),
    );
  }
}

class _AnimatedCardRow extends StatelessWidget {
  final Animation<double> animation;
  final String iconName;
  final String text;
  final double intervalStart;

  const _AnimatedCardRow({
    required this.animation,
    required this.iconName,
    required this.text,
    required this.intervalStart,
  });

  @override
  Widget build(BuildContext context) {
    final intervalEnd = (intervalStart + 0.5).clamp(0.0, 1.0);
    final curve =
        CurveTween(curve: Interval(intervalStart, intervalEnd, curve: Curves.easeOutCubic));

    final slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.5),
      end: Offset.zero,
    ).animate(animation.drive(curve));

    final fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(animation.drive(curve));

    return SlideTransition(
      position: slideAnimation,
      child: FadeTransition(
        opacity: fadeAnimation,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 16.0),
                      child: Row(
              children: [
                SvgPicture.asset(
                  iconName,
                  width: 24,
                  height: 24,
                  placeholderBuilder: (context) => Container(
                    width: 24,
                    height: 24,
                    color: Colors.red.withOpacity(0.3),
                    child: const Icon(Icons.error, color: Colors.red, size: 16),
                  ),
                ),
                const SizedBox(width: 16),
              Expanded(
                child: Text(
                  text,
                  style: const TextStyle(
                    color: Color(0xFFEFEBEB),
                    fontSize: 15,
                    fontFamily: 'SF Pro Display',
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class GenerativeTextFeedback extends StatefulWidget {
  const GenerativeTextFeedback({super.key});

  @override
  _GenerativeTextFeedbackState createState() => _GenerativeTextFeedbackState();
}

class _GenerativeTextFeedbackState extends State<GenerativeTextFeedback>
    with TickerProviderStateMixin {
  late final AnimationController _driftController;
  late final AnimationController _shimmerController;
  late final Animation<double> _driftAnimation;

  int _textIndex = 0;
  Timer? _textSwapTimer;
  final List<String> _feedbackTexts = [
    'Analyzing your query...',
    'Consulting knowledge base...',
    'Synthesizing a response...',
    'Almost there...',
  ];

  @override
  void initState() {
    super.initState();

    _driftController = AnimationController(
      duration: const Duration(milliseconds: 2500),
      vsync: this,
    )..repeat(reverse: true);
    _driftAnimation = Tween<double>(begin: -2.0, end: 2.0).animate(
      CurvedAnimation(
        parent: _driftController,
        curve: Curves.easeInOutSine,
      ),
    );

    _shimmerController = AnimationController(
      duration: const Duration(milliseconds: 1800),
      vsync: this,
    )..repeat();

    _scheduleNextSwap();
  }

  void _scheduleNextSwap() {
    // 500ms to 1500ms randomized delay for text swap
    final nextDelayMs = 500 + math.Random().nextInt(1000);
    _textSwapTimer?.cancel();
    _textSwapTimer = Timer(Duration(milliseconds: nextDelayMs), () {
      if (!mounted) return;
      setState(() {
        _textIndex = (_textIndex + 1) % _feedbackTexts.length;
      });
      _scheduleNextSwap();
    });
  }

  @override
  void dispose() {
    _driftController.dispose();
    _shimmerController.dispose();
    _textSwapTimer?.cancel();
    super.dispose();
  }

  Widget _buildCrossfadeText(Color color) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 300),
      switchInCurve: Curves.easeInOut,
      switchOutCurve: Curves.easeInOut,
      layoutBuilder: (Widget? currentChild, List<Widget> previousChildren) {
        return Stack(
          alignment: Alignment.centerLeft,
          children: <Widget>[
            ...previousChildren,
            if (currentChild != null) currentChild,
          ],
        );
      },
      transitionBuilder: (Widget child, Animation<double> animation) {
        return FadeTransition(opacity: animation, child: child);
      },
      child: Text(
        _feedbackTexts[_textIndex],
        key: ValueKey<int>(_textIndex),
        style: TextStyle(
          color: color,
          fontSize: 16,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _driftAnimation,
      builder: (context, child) {
        return Transform.translate(
          offset: Offset(0, _driftAnimation.value),
          child: child,
        );
      },
      child: Stack(
        alignment: Alignment.centerLeft,
        children: [
          // Base text (always visible)
          _buildCrossfadeText(Colors.white.withOpacity(0.7)),

          // Light diagonal shimmer overlay, clipped to text using ShaderMask
          Positioned.fill(
            child: AnimatedBuilder(
              animation: _shimmerController,
              builder: (context, _) {
                final gradient = LinearGradient(
                  colors: [
                    Colors.transparent,
                    Colors.white.withOpacity(0.40),
                    Colors.transparent,
                  ],
                  stops: const [0.30, 0.50, 0.70],
                  begin: const Alignment(-1.0, -1.0),
                  end: const Alignment(1.0, 1.0),
                  transform: _DiagonalSlide(_shimmerController.value),
                );

                return ShaderMask(
                  blendMode: BlendMode.srcATop,
                  shaderCallback: (bounds) => gradient.createShader(
                    Rect.fromLTWH(0, 0, bounds.width, bounds.height),
                  ),
                  child: _buildCrossfadeText(Colors.white.withOpacity(0.9)),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _DiagonalSlide extends GradientTransform {
  final double progress;

  const _DiagonalSlide(this.progress);

  @override
  Matrix4? transform(Rect bounds, {TextDirection? textDirection}) {
    final dx = bounds.width * 1.4 * (progress - 0.5);
    final dy = bounds.height * 1.4 * (progress - 0.5);
    return Matrix4.translationValues(dx, dy, 0.0);
  }
}

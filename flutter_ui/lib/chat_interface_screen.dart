// flutter_ui/lib/chat_interface_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'dart:math' as math;

class ChatInterfaceScreen extends StatefulWidget {
  const ChatInterfaceScreen({super.key});

  @override
  State<ChatInterfaceScreen> createState() => _ChatInterfaceScreenState();
}

class _ChatInterfaceScreenState extends State<ChatInterfaceScreen> {
  final List<String> _messages = [];
  final TextEditingController _textController = TextEditingController();
  // **NEW: State variable to control the background image opacity**
  double _yImageOpacity = 1.0;

  void _sendMessage() {
    if (_textController.text.isNotEmpty) {
      setState(() {
        _messages.add(_textController.text);
        _textController.clear();
        FocusScope.of(context).unfocus(); // Dismiss keyboard

        // **NEW: If this is the first message, reduce the opacity**
        if (_yImageOpacity == 1.0) {
          _yImageOpacity = 0.15; // Set to a subtle 15% opacity
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF2F2B2B),
      body: SafeArea(
        child: Stack(
          children: [
            // **NEW: Wrapped the image in an AnimatedOpacity widget**
            AnimatedOpacity(
              opacity: _yImageOpacity,
              duration: const Duration(milliseconds: 500),
              curve: Curves.easeInOut,
              child: Positioned(
                top: 160,
                left: 0,
                right: 0,
                child: Center(
                  child: Image.asset(
                    'assets/images/y_black.png',
                    width: 312,
                    height: 486,
                    fit: BoxFit.contain,
                  ),
                ),
              ),
            ),
            Column(
              children: [
                const Align(
                  alignment: Alignment.topRight,
                  child: Padding(
                    padding: EdgeInsets.only(top: 16.0, right: 26.0),
                    child: ModelSelectionCard(),
                  ),
                ),
                Expanded(child: _buildChatMessages()),
                ChatInputBar(
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
    return ListView.builder(
      padding: const EdgeInsets.all(16.0),
      reverse: true,
      itemCount: _messages.length,
      itemBuilder: (context, index) {
        final message = _messages.reversed.toList()[index];
        return Align(
          alignment: Alignment.centerRight,
          child: Container(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.7,
            ),
            margin: const EdgeInsets.symmetric(vertical: 5.0),
            padding:
                const EdgeInsets.symmetric(horizontal: 14.0, vertical: 10.0),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12.47),
              color: const Color(0xFF433F3F),
            ),
            child: Text(
              message,
              style: TextStyle(color: Colors.white.withOpacity(0.9), fontSize: 16),
            ),
          ),
        );
      },
    );
  }
}

class ModelSelectionCard extends StatefulWidget {
  const ModelSelectionCard({super.key});

  @override
  State<ModelSelectionCard> createState() => _ModelSelectionCardState();
}

class _ModelSelectionCardState extends State<ModelSelectionCard> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _heightAnimation;
  String _selectedModel = "model";
  bool _isExpanded = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 350),
    );
    _heightAnimation = Tween<double>(begin: 45.0, end: 135.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
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
      animation: _controller,
      builder: (context, child) {
        return Container(
          width: 140,
          height: _heightAnimation.value,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8.0),
            gradient: const RadialGradient(
              center: Alignment.center,
              radius: 0.7,
              colors: [
                Color.fromRGBO(91, 86, 86, 0.8),
                Color.fromRGBO(72, 73, 71, 0.8),
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
                _buildCollapsedView(),
                if (!_controller.isDismissed) _buildExpandedOptions(),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildCollapsedView() {
    return GestureDetector(
      onTap: _toggleExpanded,
      child: Container(
        height: 45,
        padding: const EdgeInsets.symmetric(horizontal: 12.0),
        child: Row(
          children: [
            SvgPicture.asset('assets/images/model_icon.svg', width: 27, height: 27),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                _selectedModel,
                style: const TextStyle(
                  fontFamily: 'PP Mondwest',
                  fontSize: 19,
                  color: Color.fromRGBO(255, 255, 255, 0.8),
                  fontWeight: FontWeight.w400,
                ),
                overflow: TextOverflow.ellipsis,
                maxLines: 1,
              ),
            ),
            AnimatedRotation(
              turns: _isExpanded ? 0.5 : 0,
              duration: const Duration(milliseconds: 300),
              child: const Icon(Icons.keyboard_arrow_down, color: Colors.white70, size: 20),
            ),
          ],
        ),
      ),
    );
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
      curve: Interval(delay, (delay + 0.6).clamp(0.0, 1.0), curve: Curves.easeOutCubic),
    );

    return SlideTransition(
      position: Tween<Offset>(begin: const Offset(0, -0.5), end: Offset.zero).animate(curvedAnimation),
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

class AnimatedExpandIcon extends StatelessWidget {
  final bool isExpanded;
  const AnimatedExpandIcon({super.key, required this.isExpanded});

  @override
  Widget build(BuildContext context) {
    return AnimatedRotation(
      turns: isExpanded ? 0.5 : 0.0,
      duration: const Duration(milliseconds: 300),
      child: const Icon(Icons.expand_more, color: Colors.white54),
    );
  }
}

class ChatInputBar extends StatefulWidget {
  final TextEditingController textController;
  final VoidCallback onSendMessage;

  const ChatInputBar({
    super.key,
    required this.textController,
    required this.onSendMessage,
  });

  @override
  State<ChatInputBar> createState() => _ChatInputBarState();
}

class _ChatInputBarState extends State<ChatInputBar> with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _heightAnimation;
  bool _isExpanded = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    _heightAnimation = Tween<double>(begin: 65.0, end: 280.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    widget.textController.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  void _toggleExpand() {
    setState(() {
      _isExpanded = !_isExpanded;
      if (_isExpanded) {
        _animationController.forward();
      } else {
        _animationController.reverse();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(28.0, 16.0, 28.0, 32.0),
      child: AnimatedBuilder(
        animation: _heightAnimation,
        builder: (context, child) {
          return Container(
            height: _heightAnimation.value,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12.47),
              color: const Color(0xFF433F3F),
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
                  _buildTopInputRow(),
                  if (_animationController.value > 0) _buildExpandedContent(),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildTopInputRow() {
    const textStyle = TextStyle(
      color: Color.fromRGBO(255, 255, 255, 0.70),
      fontSize: 16.24,
      fontFamily: 'PP Mondwest',
      fontWeight: FontWeight.w400,
    );
    return Container(
      height: 65,
      padding: const EdgeInsets.symmetric(horizontal: 8.0),
      child: Row(
        children: [
          IconButton(
            icon: AnimatedExpandIcon(isExpanded: _isExpanded),
            onPressed: _toggleExpand,
          ),
          Expanded(
            child: TextField(
              controller: widget.textController,
              maxLines: 1,
              style: textStyle,
              decoration: const InputDecoration(
                hintText: 'What are the most sought after skills ?..',
                hintStyle: textStyle,
                border: InputBorder.none,
              ),
            ),
          ),
          _buildSendButton(),
        ],
      ),
    );
  }

  Widget _buildExpandedContent() {
    return FadeTransition(
      opacity: _animationController,
      child: Column(
        children: [
          const Divider(color: Colors.white24, height: 1),
          const SizedBox(height: 15),
          _AnimatedCardRow(
            animation: _animationController,
            iconName: 'axe_icon.svg',
            text: 'The Resume Strategist',
            intervalStart: 0.1,
          ),
          _AnimatedCardRow(
            animation: _animationController,
            iconName: 'boxes_icon.svg',
            text: 'The Chamber of Trials',
            intervalStart: 0.2,
          ),
          _AnimatedCardRow(
            animation: _animationController,
            iconName: 'battery_charging_icon.svg',
            text: 'The Last-Minute Gambit',
            intervalStart: 0.3,
          ),
          _AnimatedCardRow(
            animation: _animationController,
            iconName: 'signal_icon.svg',
            text: 'The Radar (incl. live feed of policies)',
            intervalStart: 0.4,
          ),
        ],
      ),
    );
  }
  
  Widget _buildSendButton() {
    bool hasText = widget.textController.text.isNotEmpty;
    return Container(
      width: 45,
      height: 45,
      decoration: BoxDecoration(
        color: hasText ? Colors.white : Colors.black.withOpacity(0.2),
        shape: BoxShape.circle,
      ),
      child: IconButton(
        icon: Icon(
          Icons.arrow_upward,
          size: 22,
          color: hasText ? const Color(0xFF433F3F) : Colors.white54,
        ),
        onPressed: hasText ? widget.onSendMessage : null,
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
    final curve = CurveTween(curve: Interval(intervalStart, intervalEnd, curve: Curves.easeOutCubic));

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
              SvgPicture.asset('assets/images/$iconName', width: 24, height: 24),
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
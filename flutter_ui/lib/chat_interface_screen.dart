// flutter_ui/lib/chat_interface_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ChatInterfaceScreen extends StatefulWidget {
  const ChatInterfaceScreen({super.key});

  @override
  State<ChatInterfaceScreen> createState() => _ChatInterfaceScreenState();
}

class _ChatInterfaceScreenState extends State<ChatInterfaceScreen> {
  final List<Map<String, String>> _messages = [];
  final TextEditingController _textController = TextEditingController();
  final String _baseUrl = 'http://127.0.0.1:8000';
  double _yImageOpacity = 1.0;

  void _sendMessage() async {
    if (_textController.text.isNotEmpty) {
      final userMessage = _textController.text;
      setState(() {
        _messages.insert(0, {'sender': 'user', 'text': userMessage});
        if (_yImageOpacity == 1.0) {
          _yImageOpacity = 0.15; // Fade out the background
        }
        _textController.clear();
        FocusScope.of(context).unfocus();
      });

      try {
        final response = await http.post(
          Uri.parse('$_baseUrl/query'),
          headers: {'Content-Type': 'application/json'},
          body: json.encode({
            'question': userMessage,
            'top_k': 3,
            'filters': {},
          }),
        );

        if (response.statusCode == 200) {
          final data = json.decode(response.body);
          setState(() {
            _messages.insert(0, {'sender': 'bot', 'text': data['answer']});
          });
        } else {
          setState(() {
            _messages.insert(0,
                {'sender': 'bot', 'text': 'Error: ${response.statusCode}'});
          });
        }
      } catch (e) {
        setState(() {
          _messages.insert(
              0, {'sender': 'bot', 'text': 'Error: Could not connect.'});
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF151515),
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
                const Align(
                  alignment: Alignment.topRight,
                  child: Padding(
                    padding: EdgeInsets.only(top: 38.0, right: 26.0),
                    child: _ModelSelectionCard(),
                  ),
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
    return ListView.builder(
      padding: const EdgeInsets.all(16.0),
      reverse: true,
      itemCount: _messages.length,
      itemBuilder: (context, index) {
        final message = _messages[index];
        final isUserMessage = message['sender'] == 'user';
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
              color: isUserMessage
                  ? const Color(0xFF433F3F)
                  : const Color(0xFF2A2A2A),
            ),
            child: Text(
              message['text']!,
              style:
                  TextStyle(color: Colors.white.withOpacity(0.9), fontSize: 16),
            ),
          ),
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
                              fontFamily: 'PP NeueBit',
                              fontWeight: FontWeight.w700,
                              fontSize: 18,
                            ),
                            decoration: const InputDecoration(
                              hintText:
                                  'What are the most sought after skills ?..',
                              hintStyle: TextStyle(
                                color: Color.fromRGBO(255, 255, 255, 0.70),
                                fontSize: 18,
                                fontFamily: 'PP NeueBit',
                                fontWeight: FontWeight.w700,
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

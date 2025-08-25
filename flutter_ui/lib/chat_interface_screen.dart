import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:video_player/video_player.dart';

class ChatInterfaceScreen extends StatefulWidget {
  const ChatInterfaceScreen({super.key});

  @override
  State<ChatInterfaceScreen> createState() => _ChatInterfaceScreenState();
}

class _ChatInterfaceScreenState extends State<ChatInterfaceScreen> {
  final TextEditingController _textController = TextEditingController();
  VideoPlayerController? _videoController;
  bool _isVideoInitialized = false;
  final List<Map<String, dynamic>> _messages = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _initializeVideo();
  }

  Future<void> _initializeVideo() async {
    try {
      _videoController = VideoPlayerController.asset('assets/videos/glyph_dither.mp4');
      await _videoController!.initialize();
      await _videoController!.setLooping(true);
      await _videoController!.play();
      setState(() {
        _isVideoInitialized = true;
      });
    } catch (e) {
      // Handle video initialization error silently in production
      debugPrint('Error initializing video: $e');
    }
  }

  void _sendMessage() {
    if (_textController.text.trim().isEmpty) return;
    
    final userMessage = _textController.text.trim();
    setState(() {
      _messages.add({
        'text': userMessage,
        'isUser': true,
        'timestamp': DateTime.now(),
      });
      _isLoading = true;
    });
    
    _textController.clear();
    
    // Simulate AI response (replace with actual API call)
    Future.delayed(const Duration(seconds: 2), () {
      setState(() {
        _messages.add({
          'text': 'I\'m processing your request. This is where the AI response will appear.',
          'isUser': false,
          'timestamp': DateTime.now(),
        });
        _isLoading = false;
      });
    });
  }

  @override
  void dispose() {
    _videoController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF363232),
      body: Center(
        child: SizedBox(
          width: 393,
          height: 852,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Background Video - Using exported Unicorn Studio video
              if (_isVideoInitialized && _videoController != null)
                Positioned.fill(
                  child: FittedBox(
                    fit: BoxFit.cover,
                    child: SizedBox(
                      width: _videoController!.value.size.width,
                      height: _videoController!.value.size.height,
                      child: VideoPlayer(_videoController!),
                    ),
                  ),
                ),

              // Header with Hamburger Menu and Title
              Positioned(
                left: 25,
                top: 31,
                right: 25,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    CustomPaint(
                      size: const Size(24, 24),
                      painter: _HamburgerMenuPainter(),
                    ),
                    const Text(
                      'Y^2',
                      style: TextStyle(
                        fontFamily: 'That That New Pixel Test',
                        fontSize: 38,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(width: 24), // Spacer for balance
                  ],
                ),
              ),

              // Chat Messages Area
              Positioned(
                top: 120, // Below header
                left: 16,
                right: 16,
                bottom: 100, // Above input field
                child: _messages.isEmpty
                    ? const Center(
                        child: Text(
                          'Ask me anything about placements...',
                          style: TextStyle(
                            color: Colors.white70,
                            fontSize: 16,
                            fontFamily: 'ppmondwest',
                          ),
                        ),
                      )
                    : ListView.builder(
                        reverse: true,
                        itemCount: _messages.length + (_isLoading ? 1 : 0),
                        itemBuilder: (context, index) {
                          if (index == 0 && _isLoading) {
                            return Container(
                              margin: const EdgeInsets.only(bottom: 16),
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: const Row(
                                children: [
                                  SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                    ),
                                  ),
                                  SizedBox(width: 12),
                                  Text(
                                    'Thinking...',
                                    style: TextStyle(
                                      color: Colors.white70,
                                      fontSize: 14,
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }
                          
                          final messageIndex = _isLoading ? index - 1 : index;
                          final message = _messages[messageIndex];
                          final isUser = message['isUser'] as bool;
                          
                          return Container(
                            margin: const EdgeInsets.only(bottom: 16),
                            child: Row(
                              mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
                              children: [
                                Container(
                                  constraints: BoxConstraints(
                                    maxWidth: MediaQuery.of(context).size.width * 0.7,
                                  ),
                                  padding: const EdgeInsets.all(16),
                                  decoration: BoxDecoration(
                                    color: isUser 
                                        ? Colors.white.withValues(alpha: 0.2)
                                        : Colors.black.withValues(alpha: 0.3),
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(
                                      color: Colors.white.withValues(alpha: 0.1),
                                      width: 1,
                                    ),
                                  ),
                                  child: Text(
                                    message['text'] as String,
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 14,
                                      fontFamily: 'ppmondwest',
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
              ),

              // Functional Input Field with new Figma Specs
              Positioned(
                left: 16,
                bottom: 27,
                right: 16,
                child: Container(
                  width: 361, // Exact width from Figma
                  height: 50, // Exact height from Figma
                  padding: const EdgeInsets.fromLTRB(6, 11, 8.557, 11.986), // Exact padding from Figma
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(12.468), // Exact border-radius from Figma
                    border: Border.all(
                      color: const Color.fromRGBO(255, 255, 255, 0.56), // Exact color from Figma
                      width: 1.039, // Exact border width from Figma
                    ),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      // Green dots icon - positioned exactly as per Figma
                      Padding(
                        padding: const EdgeInsets.only(left: 6, top: 11), // Exact positioning from Figma
                        child: SvgPicture.asset(
                          'assets/images/green_dot_icon.svg',
                          width: 28, // Exact width from Figma
                          height: 28, // Exact height from Figma
                        ),
                      ),
                      const SizedBox(width: 5.429), // Exact gap from Figma
                      Expanded(
                        child: TextField(
                          controller: _textController,
                          style: const TextStyle(
                            color: Colors.white,
                            fontFamily: 'ppmondwest',
                            fontSize: 17.023, // Exact font size from Figma
                          ),
                          decoration: const InputDecoration(
                            hintText: 'I\'m not here for chit-chat. Aim, fire, and I deliver',
                            hintStyle: TextStyle(
                              color: Color.fromRGBO(255, 255, 255, 0.70), // Exact color from Figma
                              fontFamily: 'ppmondwest',
                              fontSize: 17.023, // Exact font size from Figma
                              fontWeight: FontWeight.w400,
                            ),
                            border: InputBorder.none,
                            contentPadding: EdgeInsets.only(bottom: 12),
                          ),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(
                          Icons.arrow_forward,
                          color: Colors.white,
                        ),
                        onPressed: _sendMessage, // Connect to send message function
                      ),
                    ],
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

// Custom painter for hamburger menu icon
class _HamburgerMenuPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white // Exact: stroke="white"
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0; // Exact: stroke-width="2"

    // Draw the three horizontal lines
    canvas.drawLine(const Offset(3, 6), const Offset(21, 6), paint);
    canvas.drawLine(const Offset(3, 12), const Offset(21, 12), paint);
    canvas.drawLine(const Offset(3, 18), const Offset(21, 18), paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

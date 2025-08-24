import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class ChatInterfaceScreen extends StatefulWidget {
  const ChatInterfaceScreen({super.key});

  @override
  State<ChatInterfaceScreen> createState() => _ChatInterfaceScreenState();
}

class _ChatInterfaceScreenState extends State<ChatInterfaceScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF363232), // Exact: background: #363232
      body: Center(
        child: SizedBox(
          width: 393, // Exact: width: 393px
          height: 852, // Exact: height: 852px
          child: Stack(
            children: [
              // Y Logo - Using y_logo.png with exact Figma styling
              Positioned(
                left: 51.78, // Exact: left: 51.78px
                top: 215.68, // Exact: top: 215.68px
                child: Container(
                  width: 279.834, // Exact: width: 279.834px
                  height: 435.414, // Exact: height: 435.414px
                  decoration: BoxDecoration(
                    boxShadow: [
                      BoxShadow(
                        color: const Color.fromRGBO(0, 0, 0, 0.25), // rgba(0, 0, 0, 0.25)
                        offset: const Offset(0, 4), // 0 4px
                        blurRadius: 4, // 4px
                        spreadRadius: 0, // 0
                      ),
                    ],
                  ),
                  child: Opacity(
                    opacity: 0.28, // Exact: opacity: 0.28
                    child: Image.asset(
                      'assets/images/y_logo.png',
                      width: 279.834,
                      height: 435.414,
                      fit: BoxFit.contain,
                      color: const Color.fromRGBO(255, 255, 255, 0.23), // fill: rgba(255, 255, 255, 0.23)
                      colorBlendMode: BlendMode.modulate,
                    ),
                  ),
                ),
              ),

              // Main Message - "I'm your placement co-pilot..."
              Positioned(
                left: 96, // Center the main message (393 - 200) / 2 = 96.5
                top: 300, // Position in the center area of the screen
                child: Container(
                  width: 200, // Give enough width for text
                  color: Colors.red.withValues(alpha: 0.3), // DEBUG: Make text area visible
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        'I\'m your placement co-pilot.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontFamily: 'Arial', // DEBUG: Use system font instead of 'ppmondwest'
                          fontWeight: FontWeight.w400,
                          height: 1.3,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'I don\'t hold hands.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontFamily: 'Arial', // DEBUG: Use system font instead of 'ppmondwest'
                          fontWeight: FontWeight.w400,
                          height: 1.3,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'I hand you weapons.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontFamily: 'Arial', // DEBUG: Use system font instead of 'ppmondwest'
                          fontWeight: FontWeight.w400,
                          height: 1.3,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Input Field - Frame 2 with exact specifications
              Positioned(
                left: 16, // Exact: left: 16px
                top: 775, // Exact: top: 775px
                child: Container(
                  width: 361, // Exact: width: 361px
                  height: 50, // Exact: height: 50px
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(12.47), // Exact: border-radius: 12.47px
                    border: Border.all(
                      color: const Color.fromRGBO(255, 255, 255, 0.56), // Exact: rgba(255, 255, 255, 0.56)
                      width: 1.04, // Exact: outline: 1.04px
                    ),
                  ),
                  child: Stack(
                    children: [
                      // Text: "I'm not here for chit-chat. Aim, fire, and I deliver"
                      Positioned(
                        left: 38.44, // Exact: left: 38.44px
                        top: 15.58, // Exact: top: 15.58px
                        child: SizedBox(
                          width: 280, // Give enough width for text to wrap properly
                          child: Text(
                            'I\'m not here for chit-chat. Aim, fire, and I deliver',
                            style: TextStyle(
                              color: const Color.fromRGBO(255, 255, 255, 0.70), // Exact: rgba(255, 255, 255, 0.70)
                              fontSize: 17.02, // Exact: font-size: 17.02px
                              fontFamily: 'ppmondwest', // Exact: font-family: PP Mondwest
                              fontWeight: FontWeight.w400, // Exact: font-weight: 400
                            ),
                            softWrap: true, // Enable text wrapping
                            overflow: TextOverflow.visible, // Allow text to be visible
                          ),
                        ),
                      ),
                      // Green dots icon
                      Positioned(
                        left: 6, // Exact: left: 6px
                        top: 11, // Exact: top: 11px
                        child: SvgPicture.asset(
                          'assets/images/green_dot_icon.svg',
                          width: 28, // Exact: width="28"
                          height: 28, // Exact: height="28"
                        ),
                      ),
                      // Send button (arrow icon)
                      Positioned(
                        right: 12, // Position on the right side
                        top: 11, // Align with the green dots icon
                        child: Icon(
                          Icons.arrow_forward,
                          color: Colors.white,
                          size: 24,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Hamburger menu icon
              Positioned(
                left: 25, // Exact: left: 25px
                top: 31, // Exact: top: 31px
                child: CustomPaint(
                  size: const Size(24, 24), // Exact: width="24" height="24"
                  painter: _HamburgerMenuPainter(),
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

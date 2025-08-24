import 'package:flutter/material.dart';

class ChatInterfaceScreen extends StatefulWidget {
  final String selectedSpecialization;
  
  const ChatInterfaceScreen({super.key, required this.selectedSpecialization});

  @override
  State<ChatInterfaceScreen> createState() => _ChatInterfaceScreenState();
}

class _ChatInterfaceScreenState extends State<ChatInterfaceScreen>
    with TickerProviderStateMixin {
  late AnimationController _fadeController;
  late AnimationController _slideController;
  late AnimationController _scaleController;
  
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    
    _fadeController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    
    _slideController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    
    _scaleController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeOut,
    ));
    
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.3),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _slideController,
      curve: Curves.easeOutCubic,
    ));
    
    _scaleAnimation = Tween<double>(
      begin: 0.8,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _scaleController,
      curve: Curves.elasticOut,
    ));
    
    _startAnimations();
  }

  void _startAnimations() async {
    await Future.delayed(const Duration(milliseconds: 200));
    _fadeController.forward();
    await Future.delayed(const Duration(milliseconds: 300));
    _slideController.forward();
    await Future.delayed(const Duration(milliseconds: 200));
    _scaleController.forward();
  }

  @override
  void dispose() {
    _fadeController.dispose();
    _slideController.dispose();
    _scaleController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF363232), // Exact: background: #363232
      body: Center(
        child: Container(
          width: 393, // Exact: width: 393px
          height: 852, // Exact: height: 852px
          child: Stack(
            children: [
              // Y logo - Large background logo using actual y_logo.png
              ScaleTransition(
                scale: _scaleAnimation,
                child: FadeTransition(
                  opacity: _fadeAnimation,
                  child: Positioned(
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
                ),
              ),
              
              // Main message - "I'm your placement co-pilot..." (exact positioning)
              SlideTransition(
                position: _slideAnimation,
                child: FadeTransition(
                  opacity: _fadeAnimation,
                  child: Positioned(
                    left: 140.82, // Exact: left: 140.82px
                    top: 395.10, // Exact: top: 395.10px
                    child: Container(
                      width: 200, // Adjusted for text content to avoid cut-off
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            'I\'m your placement co-pilot.',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontFamily: 'PP Mondwest',
                              fontWeight: FontWeight.w400,
                              height: 1.3,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'I don\'t hold hands.',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontFamily: 'PP Mondwest',
                              fontWeight: FontWeight.w400,
                              height: 1.3,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'I hand you weapons.',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontFamily: 'PP Mondwest',
                              fontWeight: FontWeight.w400,
                              height: 1.3,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              
              // Frame 2 - Input field at bottom (exact positioning)
              FadeTransition(
                opacity: _fadeAnimation,
                child: Positioned(
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
                          child: Text(
                            'I\'m not here for chit-chat. Aim, fire, and I deliver',
                            style: TextStyle(
                              color: const Color.fromRGBO(255, 255, 255, 0.7), // Exact: rgba(255, 255, 255, 0.70)
                              fontSize: 17.023, // Exact: font-size: 17.023px
                              fontFamily: 'PP Mondwest', // Exact: font-family: PP Mondwest
                              fontStyle: FontStyle.normal, // Exact: font-style: normal
                              fontWeight: FontWeight.w400, // Exact: font-weight: 400
                              height: 1.0, // Exact: line-height: normal
                            ),
                          ),
                        ),
                        // Icon_2 - Green dots icon (exact positioning)
                        Positioned(
                          left: 6, // Exact: left: 6px
                          top: 11, // Exact: top: 11px
                          child: Container(
                            width: 28, // Exact: width: 28
                            height: 28, // Exact: height: 28
                            child: CustomPaint(
                              painter: _GreenDotsPainter(),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              
              // Hamburger menu icon - Top left (exact positioning)
              FadeTransition(
                opacity: _fadeAnimation,
                child: Positioned(
                  left: 25, // Exact: left: 25px
                  top: 31, // Exact: top: 31px
                  child: Container(
                    width: 24, // Exact: width: 24
                    height: 24, // Exact: height: 24
                    child: CustomPaint(
                      painter: _HamburgerMenuPainter(),
                    ),
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

// Custom painter for the green dots icon - exact SVG implementation
class _GreenDotsPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF15B720).withValues(alpha: 0.7) // Exact: fill="#15B720" fill-opacity="0.7"
      ..style = PaintingStyle.fill;

    // Draw the exact green dots pattern from the SVG paths
    // Top row dots
    canvas.drawCircle(Offset(2.81395, 11.8185), 0.5, paint);
    canvas.drawCircle(Offset(5.90928, 15.1952), 0.5, paint);
    canvas.drawCircle(Offset(10.9744, 15.1952), 0.5, paint);
    canvas.drawCircle(Offset(16.0394, 15.1952), 0.5, paint);
    canvas.drawCircle(Offset(21.1045, 15.1952), 0.5, paint);
    
    // Middle row dots
    canvas.drawCircle(Offset(8.44182, 10.6929), 0.5, paint);
    canvas.drawCircle(Offset(13.5069, 10.6929), 0.5, paint);
    canvas.drawCircle(Offset(18.572, 10.6929), 0.5, paint);
    
    // Bottom row dots
    canvas.drawCircle(Offset(8.44182, 19.6975), 0.5, paint);
    canvas.drawCircle(Offset(13.5069, 19.6975), 0.5, paint);
    canvas.drawCircle(Offset(18.572, 19.6975), 0.5, paint);
    
    // Bottom center dots
    canvas.drawCircle(Offset(12.3813, 22.5115), 0.5, paint);
    canvas.drawCircle(Offset(14.6325, 22.5115), 0.5, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

// Custom painter for the hamburger menu icon - exact SVG implementation
class _HamburgerMenuPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0; // Exact: stroke-width="2"

    // Draw the three horizontal lines from the SVG
    // First line: M3 6H21
    canvas.drawLine(
      const Offset(3, 6),
      const Offset(21, 6),
      paint,
    );
    
    // Second line: M3 12H21
    canvas.drawLine(
      const Offset(3, 12),
      const Offset(21, 12),
      paint,
    );
    
    // Third line: M3 18H21
    canvas.drawLine(
      const Offset(3, 18),
      const Offset(21, 18),
      paint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

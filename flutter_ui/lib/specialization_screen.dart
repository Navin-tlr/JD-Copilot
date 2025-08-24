import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'chat_interface_screen.dart';

class SpecializationScreen extends StatefulWidget {
  const SpecializationScreen({super.key});

  @override
  State<SpecializationScreen> createState() => _SpecializationScreenState();
}

class _SpecializationScreenState extends State<SpecializationScreen>
    with TickerProviderStateMixin {
  late AnimationController _fadeController;
  late AnimationController _scaleController;
  late AnimationController _successController;
  late Animation<double> _fadeAnimation;
  late Animation<double> _scaleAnimation;

  String? _selectedSpecialization;

  @override
  void initState() {
    super.initState();
    
    // Initialize controllers with Apple-like timing
    _fadeController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    
    _scaleController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );

    _successController = AnimationController(
      duration: const Duration(milliseconds: 400),
      vsync: this,
    );

    // Create Apple-style animations
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeOut,
    ));

    _scaleAnimation = Tween<double>(
      begin: 0.8,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _scaleController,
      curve: Curves.easeOutBack,
    ));



    // Start animations with Apple-like staggering
    _startAnimations();
  }

  void _startAnimations() async {
    // Add subtle haptic feedback
    HapticFeedback.lightImpact();
    
    // Start animations with staggered timing
    _scaleController.forward();
    await Future.delayed(const Duration(milliseconds: 100));
    _fadeController.forward();
  }

  @override
  void dispose() {
    _fadeController.dispose();
    _scaleController.dispose();
    _successController.dispose();
    super.dispose();
  }

  void _onSpecializationSelected(String specializationId) async {
    if (_selectedSpecialization == specializationId) return;

    // Apple-style haptic feedback
    HapticFeedback.mediumImpact();

    setState(() {
      _selectedSpecialization = specializationId;
    });

    // Enhanced animation sequence
    await _playSelectionAnimation();
    
    // Navigate to chat interface with smooth transition
    if (mounted) {
      Navigator.of(context).pushReplacement(
        PageRouteBuilder(
          pageBuilder: (context, animation, secondaryAnimation) => 
              ChatInterfaceScreen(),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(
              opacity: CurvedAnimation(
                parent: animation,
                curve: Curves.easeInOut,
              ),
              child: SlideTransition(
                position: Tween<Offset>(
                  begin: const Offset(0, 0.3),
                  end: Offset.zero,
                ).animate(CurvedAnimation(
                  parent: animation,
                  curve: Curves.easeOutCubic,
                )),
                child: child,
              ),
            );
          },
          transitionDuration: const Duration(milliseconds: 800),
        ),
      );
    }
  }

  Future<void> _playSelectionAnimation() async {
    // Trigger success animation
    _successController.forward();
    
    // Add success haptic feedback
    HapticFeedback.heavyImpact();
    
    // Wait for animation to complete
    await Future.delayed(const Duration(milliseconds: 600));
  }





  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Container(
          width: 393, // Exact Figma frame width - same as onboarding
          height: 852, // Exact Figma frame height - same as onboarding
          child: Stack(
            children: [
              // Background gradient (subtle Apple-style)
              Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.white,
                      Colors.grey.shade50,
                    ],
                  ),
                ),
              ),

              // Main content
              Positioned.fill(
                child: Stack(
                  children: [
                    // Specialization card with animation - positioned according to new Figma
                    Positioned(
                      left: 44, // Exact Figma: left: 44px
                      top: 160, // Exact Figma: top: 160px
                      child: AnimatedBuilder(
                        animation: _scaleAnimation,
                        builder: (context, child) {
                          return Transform.scale(
                            scale: _scaleAnimation.value,
                            child: FadeTransition(
                              opacity: _fadeAnimation,
                              child: Container(
                                width: 306, // Exact Figma width
                                height: 531, // Exact Figma height
                                decoration: BoxDecoration(
                                  color: Colors.black, // Exact Figma: bg-[#000000]
                                  borderRadius: BorderRadius.circular(15), // Exact Figma: rounded-[15px]
                                ),
                                child: Stack(
                                  children: [
                                    // Title positioned exactly as in Figma - Updated positioning
                                    Positioned(
                                      left: 45, // Exact Figma: left: 45px
                                      top: 76, // Exact Figma: top: 76px
                                      child: Text(
                                        'Select Your\nSpecialization',
                                        textAlign: TextAlign.center,
                                        style: TextStyle(
                                          fontFamily: 'PP Mondwest',
                                          fontSize: 39, // New Figma: font-size: 39px
                                          fontWeight: FontWeight.w400, // New Figma: font-weight: 400
                                          color: Colors.white,
                                          height: 35/39, // New Figma: line-height: 35px
                                        ),
                                      ),
                                    ),

                                    // Cursor/Arrow positioned exactly as in Figma - Updated positioning
                                    Positioned(
                                      left: 120, // New Figma: left: 120px
                                      top: 82, // New Figma: top: 82px
                                      child: Container(
                                        width: 208, // Exact Figma width
                                        height: 141.71, // Exact Figma height
                                        child: Stack(
                                          children: [
                                            // Arrow border (white outline)
                                            Positioned(
                                              left: 92.57, // Exact Figma position
                                              top: 50.43, // Exact Figma position
                                              child: CustomPaint(
                                                size: Size(27, 41),
                                                painter: _ArrowBorderPainter(),
                                              ),
                                            ),
                                            // Arrow fill (black)
                                            Positioned(
                                              left: 94.86, // Exact Figma position
                                              top: 55.95, // Exact Figma position
                                              child: CustomPaint(
                                                size: Size(20, 34),
                                                painter: _ArrowPainter(),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),

                                    // Marketing button - Exact Figma positioning
                                    Positioned(
                                      left: 27, // Exact Figma: left: 27px
                                      top: 200, // Exact Figma: top: 200px
                                      child: _FigmaSpecializationButton(
                                        title: 'Marketing',
                                        isSelected: _selectedSpecialization == 'marketing',
                                        onTap: () => _onSpecializationSelected('marketing'),
                                      ),
                                    ),

                                    // Lean Operations & Systems button
                                    Positioned(
                                      left: 27, // Exact Figma: left: 27px
                                      top: 257, // Exact Figma: top: 257px
                                      child: _FigmaSpecializationButton(
                                        title: 'Lean Operations & Systems',
                                        isSelected: _selectedSpecialization == 'lean_operations',
                                        onTap: () => _onSpecializationSelected('lean_operations'),
                                      ),
                                    ),

                                    // Finance button
                                    Positioned(
                                      left: 27, // Exact Figma: left: 27px
                                      top: 316, // Exact Figma: top: 316px
                                      child: _FigmaSpecializationButton(
                                        title: 'Finance',
                                        isSelected: _selectedSpecialization == 'finance',
                                        onTap: () => _onSpecializationSelected('finance'),
                                      ),
                                    ),

                                    // Human Resources button
                                    Positioned(
                                      left: 27, // Exact Figma: left: 27px
                                      top: 373, // Exact Figma: top: 373px
                                      child: _FigmaSpecializationButton(
                                        title: 'Human Resources',
                                        isSelected: _selectedSpecialization == 'human_resources',
                                        onTap: () => _onSpecializationSelected('human_resources'),
                                      ),
                                    ),

                                    // Business Analytics button
                                    Positioned(
                                      left: 27, // Exact Figma: left: 27px
                                      top: 432, // Exact Figma: top: 432px
                                      child: _FigmaSpecializationButton(
                                        title: 'Business Analytics',
                                        isSelected: _selectedSpecialization == 'business_analytics',
                                        onTap: () => _onSpecializationSelected('business_analytics'),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SpecializationButton extends StatefulWidget {
  final String title;
  final IconData icon;
  final Color color;
  final bool isSelected;
  final VoidCallback onTap;

  const _SpecializationButton({
    required this.title,
    required this.icon,
    required this.color,
    required this.isSelected,
    required this.onTap,
  });

  @override
  State<_SpecializationButton> createState() => _SpecializationButtonState();
}

class _SpecializationButtonState extends State<_SpecializationButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 100),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 0.96,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTapDown(TapDownDetails details) {
    _controller.forward();
    HapticFeedback.lightImpact();
  }

  void _handleTapUp(TapUpDetails details) {
    _controller.reverse();
  }

  void _handleTapCancel() {
    _controller.reverse();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _scaleAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: _scaleAnimation.value,
          child: GestureDetector(
            onTapDown: _handleTapDown,
            onTapUp: _handleTapUp,
            onTapCancel: _handleTapCancel,
            onTap: widget.onTap,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              curve: Curves.easeInOut,
              width: 252, // Exact Figma width
              height: 48, // Exact Figma height (h-12 = 48px)
              decoration: BoxDecoration(
                color: widget.isSelected
                    ? widget.color.withOpacity(0.2)
                    : Colors.white.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: widget.isSelected
                      ? widget.color
                      : Colors.white.withOpacity(0.3),
                  width: widget.isSelected ? 2 : 1,
                ),
              ),
              child: Row(
                children: [
                  const SizedBox(width: 16),
                  Icon(
                    widget.icon,
                    color: widget.isSelected ? widget.color : Colors.white,
                    size: 20,
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Text(
                      widget.title,
                      style: TextStyle(
                        fontFamily: 'PP Mondwest',
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                        color: widget.isSelected ? widget.color : Colors.white,
                      ),
                    ),
                  ),
                  if (widget.isSelected)
                    Icon(
                      Icons.check_circle_rounded,
                      color: widget.color,
                      size: 20,
                    ),
                  const SizedBox(width: 16),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _AppleStyleButton extends StatefulWidget {
  final VoidCallback onPressed;
  final Widget child;
  final bool isPrimary;

  const _AppleStyleButton({
    required this.onPressed,
    required this.child,
    required this.isPrimary,
  });

  @override
  State<_AppleStyleButton> createState() => _AppleStyleButtonState();
}

class _AppleStyleButtonState extends State<_AppleStyleButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 100),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 0.96,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTapDown(TapDownDetails details) {
    _controller.forward();
    HapticFeedback.lightImpact();
  }

  void _handleTapUp(TapUpDetails details) {
    _controller.reverse();
  }

  void _handleTapCancel() {
    _controller.reverse();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _scaleAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: _scaleAnimation.value,
          child: GestureDetector(
            onTapDown: _handleTapDown,
            onTapUp: _handleTapUp,
            onTapCancel: _handleTapCancel,
            onTap: widget.onPressed,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              curve: Curves.easeInOut,
              width: double.infinity,
              height: 56,
              decoration: BoxDecoration(
                color: widget.isPrimary
                    ? Color(0xFF4E9816)
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(16),
                border: widget.isPrimary 
                    ? null 
                    : Border.all(
                        color: Colors.grey.shade200,
                        width: 1.5,
                      ),
                boxShadow: widget.isPrimary
                    ? [
                        BoxShadow(
                          color: Color(0xFF4E9816).withOpacity(0.3),
                          blurRadius: 12,
                          offset: Offset(0, 4),
                        ),
                      ]
                    : null,
              ),
              child: Center(child: widget.child),
            ),
          ),
        );
      },
    );
  }
}

// Custom widget for Figma-exact specialization buttons
class _FigmaSpecializationButton extends StatefulWidget {
  final String title;
  final bool isSelected;
  final VoidCallback onTap;

  const _FigmaSpecializationButton({
    required this.title,
    required this.isSelected,
    required this.onTap,
  });

  @override
  State<_FigmaSpecializationButton> createState() => _FigmaSpecializationButtonState();
}

class _FigmaSpecializationButtonState extends State<_FigmaSpecializationButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 100),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 0.98,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTapDown(TapDownDetails details) {
    _controller.forward();
    HapticFeedback.lightImpact();
  }

  void _handleTapUp(TapUpDetails details) {
    _controller.reverse();
  }

  void _handleTapCancel() {
    _controller.reverse();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _scaleAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: _scaleAnimation.value,
          child: GestureDetector(
            onTapDown: _handleTapDown,
            onTapUp: _handleTapUp,
            onTapCancel: _handleTapCancel,
            onTap: widget.onTap,
            child: Container(
              width: 252, // Exact Figma width from HTML (260px - 8px padding)
              height: 48, // Exact Figma height (adjusted from 56px container)
              decoration: BoxDecoration(
                color: widget.isSelected 
                    ? Color(0xFF4E9816).withOpacity(0.2)
                    : Color(0xFF1B1919), // Exact Figma: #1B1919
                borderRadius: BorderRadius.circular(15), // Matched border radius
                border: Border.all(
                  color: widget.isSelected 
                      ? Color(0xFF4E9816)
                      : Colors.white.withOpacity(0.5), // Exact Figma stroke
                  width: 0.5,
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.white.withOpacity(0.25), // Exact Figma shadow
                    blurRadius: 4,
                    offset: Offset(0, 2),
                  ),
                ],
              ),
              child: Center(
                child: Text(
                  widget.title,
                  style: TextStyle(
                    fontFamily: 'PP Mondwest',
                    fontSize: 14,
                    fontWeight: FontWeight.w400,
                    color: widget.isSelected ? Color(0xFF4E9816) : Colors.white,
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

// Custom painter for the arrow border (white outline)
class _ArrowBorderPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;

    final path = Path();
    
    // Exact path from Figma SVG
    path.moveTo(20.967, 34.7819);
    path.cubicTo(21.3679, 35.744, 20.9826, 39.3878, 18.8571, 40.2325);
    path.cubicTo(16.7316, 41.0771, 14.0159, 40.2325, 14.0159, 40.2325);
    path.lineTo(9.08809, 30.3768);
    path.lineTo(0.571411, 38.8935);
    path.lineTo(0.571411, 0.428558);
    path.lineTo(26.661, 26.5182);
    path.lineTo(16.9406, 26.5182);
    path.cubicTo(17.4176, 27.4329, 20.4577, 33.5596, 20.967, 34.7819);
    path.close();

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

// Custom painter for the arrow fill (black)
class _ArrowPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.fill;

    final path = Path();
    
    // Exact path from Figma SVG with fill rule
    path.moveTo(0.857117, 0.946777);
    path.lineTo(0.857117, 28.3753);
    path.lineTo(7.71426, 21.5182);
    path.lineTo(13.4285, 32.9468);
    path.cubicTo(13.4285, 32.9468, 14.9744, 33.44, 15.7143, 32.9468);
    path.cubicTo(16.4541, 32.4535, 17.1901, 31.4601, 16.8571, 30.6611);
    path.cubicTo(15.2853, 26.8887, 11.1428, 19.2325, 11.1428, 19.2325);
    path.lineTo(19.1428, 19.2325);
    path.lineTo(0.857117, 0.946777);
    path.close();

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

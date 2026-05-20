import 'package:flutter/material.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';

class ShimmerCard extends StatelessWidget {
  final double height;
  final double width;
  const ShimmerCard({super.key, required this.height, this.width = double.infinity});

  @override
  Widget build(BuildContext context) {
    return Container(
      width:  width,
      height: height,
      margin: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        color: AppTheme.bgLight,
        borderRadius: BorderRadius.circular(12),
      ),
    );
  }
}

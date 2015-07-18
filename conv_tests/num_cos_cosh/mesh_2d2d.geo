DefineConstant[ d = { $d$ , Name "Gmsh/Parameters/d"}];
DefineConstant[ h = { $h$ , Name "Gmsh/Parameters/h"}];
DefineConstant[ h1d = { $h1d$ , Name "Gmsh/Parameters/h1d"}];

x_l=0;
x_f=1;
x_r=2;


y_top=0.5;
y_bot=0;

x_ref = 0.1*(1-d/2);
y_ref = 0.1*(1-d/2);
hx_ref = Exp( (0.7*Log(h)+1.3*Log(h1d))/2 ); 
 
Point(1) = {x_l,  y_bot,  0, h};
Point(2) = {x_l,  y_top,  0, h};
Point(3) = {x_r,  y_bot,  0, h};
Point(4) = {x_r,  y_top,  0, h};

Point(11) = {x_f-d/2,  y_bot,  0, h1d};
Point(12) = {x_f-d/2,  y_top,  0, h1d};
Point(13) = {x_f+d/2,  y_bot,  0, h1d};
Point(14) = {x_f+d/2,  y_top,  0, h1d};

Point(21) = {x_f-x_ref,  y_bot,  0, hx_ref};
Point(22) = {x_f-x_ref,  y_top,  0, hx_ref};
Point(23) = {x_f+x_ref,  y_bot,  0, hx_ref};
Point(24) = {x_f+x_ref,  y_top,  0, hx_ref};

Point(31) = {x_f-x_ref,  y_bot+y_ref,  0, hx_ref};
Point(32) = {x_f-x_ref,  y_top-y_ref,  0, hx_ref};
Point(33) = {x_f+x_ref,  y_bot+y_ref,  0, hx_ref};
Point(34) = {x_f+x_ref,  y_top-y_ref,  0, hx_ref};

Point(41) = {x_f-d/2,  y_bot+y_ref,  0, hx_ref};
Point(42) = {x_f-d/2,  y_top-y_ref,  0, hx_ref};
Point(43) = {x_f+d/2,  y_bot+y_ref,  0, hx_ref};
Point(44) = {x_f+d/2,  y_top-y_ref,  0, hx_ref};



Line(1) = {2, 22};
Line(2) = {22, 12};
Line(3) = {12, 14};
Line(4) = {14, 24};
Line(5) = {24, 4};
Line(6) = {3, 4};
Line(7) = {24, 34};
Line(8) = {14, 44};
Line(9) = {34, 44};
Line(10) = {42, 12};
Line(11) = {22, 32};
Line(12) = {32, 42};
Line(13) = {42, 44};
Line(14) = {44, 43};
Line(15) = {42, 41};
Line(16) = {2, 1};
Line(17) = {1, 21};
Line(18) = {31, 21};
Line(19) = {41, 11};
Line(20) = {43, 13};
Line(21) = {33, 23};
Line(22) = {31, 41};
Line(23) = {43, 33};
Line(24) = {23, 13};
Line(25) = {11, 13};
Line(26) = {11, 21};
Line(27) = {41, 43};
Line(28) = {23, 3};
Line Loop(29) = {1, 11, 12, 15, -22, 18, -17, -16};
Plane Surface(30) = {29};
Line Loop(31) = {11, 12, 10, -2};
Plane Surface(32) = {31};
Line Loop(33) = {8, -9, -7, -4};
Plane Surface(34) = {33};
Line Loop(35) = {3, 8, -13, 10};
Plane Surface(36) = {35};
Line Loop(37) = {15, 27, -14, -13};
Plane Surface(38) = {37};
Line Loop(39) = {27, 20, -25, -19};
Plane Surface(40) = {39};
Line Loop(41) = {22, 19, 26, -18};
Plane Surface(42) = {41};
Line Loop(43) = {23, 21, 24, -20};
Plane Surface(44) = {43};
Line Loop(45) = {14, 23, 21, 28, 6, -5, 7, 9};
Plane Surface(46) = {45};
Physical Surface("matrix") = {30, 32, 42, 34, 46, 44};
Physical Surface("fracture") = {36, 38, 40};
Physical Line(".matrix_left") = {16};
Physical Line(".matrix_right") = {6};
Physical Line(".matrix_top") = {1, 2, 4, 5};
Physical Line(".matrix_bottom") = {17, 26, 24, 28};
Physical Line(".fracture_top") = {3};
Physical Line(".fracture_bottim") = {25};


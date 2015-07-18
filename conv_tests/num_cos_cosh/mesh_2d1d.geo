DefineConstant[ d = { $d$ , Name "Gmsh/Parameters/d"}];
DefineConstant[ h = { $h$ , Name "Gmsh/Parameters/h"}];
DefineConstant[ h1d = { $h1d$ , Name "Gmsh/Parameters/h1d"}];

y_top=+0.5;
y_bot=0;

Point(1) = {0+d/2, y_bot, 0, h};
Point(2) = {0+d/2, y_top, 0, h};
Point(3) = {1, y_bot, 0, h};
Point(4) = {1, y_top, 0, h};
Point(5) = {+2-d/2, y_bot, 0, h};
Point(6) = {+2-d/2, y_top, 0, h};

Line(7) = {1, 2};
Line(8) = {2, 4};
Line(9) = {4, 3};
Line(10) = {3, 1};
Line Loop(11) = {8, 9, 10, 7};
Plane Surface(12) = {11};
Line(13) = {4, 6};
Line(14) = {6, 5};
Line(15) = {5, 3};
Line Loop(16) = {13, 14, 15, -9};
Plane Surface(17) = {16};


Physical Surface("matrix") = { 12, 17};
Physical Line("fracture") = { 9 };
Physical Line(".matrix_right") = { 14 };
Physical Line(".matrix_left") = { 7 };
Physical Line(".matrix_top") = { 8, 13 };
Physical Line(".matrix_bottom") = { 10, 15 };
Physical Point(".fracture_top") = { 4 };
Physical Point(".fracture_bottom") = { 3 };


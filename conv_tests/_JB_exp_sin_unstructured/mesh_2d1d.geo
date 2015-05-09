DefineConstant[ d = { $d$ , Name "Gmsh/Parameters/d"}];
DefineConstant[ h = { $h$ , Name "Gmsh/Parameters/h"}];
DefineConstant[ factor = { 2 , Name "Gmsh/Parameters/factor"}];

Point(1) = {-1+d/2, 0, 0, factor*h};
Point(2) = {-1+d/2, 1, 0, factor*h};
Point(3) = {0, 0, 0, h};
Point(4) = {0, 1, 0, h};
Point(5) = {+1-d/2, 0, 0, factor*h};
Point(6) = {+1-d/2, 1, 0, factor*h};

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


Physical Surface("hornina") = { 12, 17};
Physical Line("puklina") = { 9 };
Physical Line(".right") = { 14 };
Physical Line(".left") = { 7 };
Physical Line(".no_flow") = { 8, 10, 13, 15 };
Physical Point(".no_flow_body") = { 3, 4 };


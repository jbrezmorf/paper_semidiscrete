DefineConstant[ d = { $d$ , Name "Gmsh/Parameters/d"}];
DefineConstant[ h = { $h$ , Name "Gmsh/Parameters/h"}];
//DefineConstant[ h1d = { $h1d$ , Name "Gmsh/Parameters/h1d"}];


fr_scale_left=Exp((-1+$d$)*0.5);
fr_scale_right=Exp((-1-$d$)*0.5);
scale_right=Exp(-1);

Point(1) = {-0.5, 0, 0, h};
Point(2) = {-0.5, 1, 0, h};
Point(3) = {-d/2, 0, 0, h*fr_scale_left};
Point(4) = {-d/2, 1, 0, h*fr_scale_left};
Point(7) = {+d/2, 0, 0, h*fr_scale_right};
Point(8) = {+d/2, 1, 0, h*fr_scale_right};
Point(5) = {+0.5, 0, 0, h*scale_right};
Point(6) = {+0.5, 1, 0, h*scale_right};

Line(7) = {1, 2};
Line(8) = {2, 4};
Line(9) = {4, 3};
Line(10) = {3, 1};
Line Loop(11) = {8, 9, 10, 7};
Plane Surface(12) = {11};
Line(13) = {8, 6};
Line(14) = {6, 5};
Line(15) = {5, 7};
Line(18) = {7, 8};
Line Loop(16) = {13, 14, 15, 18};
Plane Surface(17) = {16};
Line(20) = {3, 7};
Line(21) = {8, 4};
Line Loop(22) = {20, 18, 21, 9};
Plane Surface(23) = {22};


Physical Surface("hornina") = { 12, 17};
Physical Surface("puklina") = { 23 };
Physical Line(".right") = { 14 };
Physical Line(".left") = { 7 };
Physical Line(".no_flow") = { 8, 10, 13, 15 };
Physical Line(".no_flow_body") = { 20, 21 };


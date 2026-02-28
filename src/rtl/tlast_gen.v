`timescale 1ns / 1ps

module tlast_gen
#(
    parameter                            TDATA_WIDTH    = 8,
    parameter                            MAX_PKT_LENGTH = 256,
    parameter [$clog2(MAX_PKT_LENGTH):0] PKT_LENGTH     = 256
)
(
    // Clocks and resets
    input                            aclk,
    input                            resetn,
    
    // Slave interface
    input                            s_axis_tvalid,
    output                           s_axis_tready,
    input  [TDATA_WIDTH-1:0]         s_axis_tdata,
    
    // Master interface
    output                           m_axis_tvalid,
    input                            m_axis_tready,
    output                           m_axis_tlast,
    output [TDATA_WIDTH-1:0]         m_axis_tdata,
    output [$clog2(MAX_PKT_LENGTH):0] o_cnt
);

    // Internal signals
    wire new_sample;
    reg [$clog2(MAX_PKT_LENGTH):0] cnt;

    // Pass through control signals
    assign s_axis_tready = m_axis_tready;
    assign m_axis_tvalid = s_axis_tvalid;
    assign m_axis_tdata  = s_axis_tdata;

    // Count samples
    assign new_sample = s_axis_tvalid & s_axis_tready;
    
    always @ (posedge aclk) begin
        if (~resetn)
            cnt <= 0;
        else begin
            if (new_sample) begin
                if (m_axis_tlast) begin
                    cnt <= 'b1;
                end else begin
                    cnt <= cnt + 'b1;
                end
            end        
        end
    end
    
    // Generate tlast
    assign m_axis_tlast = (cnt == PKT_LENGTH) & new_sample;
    assign o_cnt = cnt;

endmodule
